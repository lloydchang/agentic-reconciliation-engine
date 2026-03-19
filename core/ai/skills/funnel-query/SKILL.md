---
name: funnel-query
description: Use when analyzing user conversion funnels and customer journey analytics. Provides standardized queries for signup → activation → paid conversion analysis, cohort comparisons, and funnel optimization insights across product metrics.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "1.0"
  category: data-analysis
  risk_level: low
  autonomy: conditional
  layer: temporal
compatibility: Requires Python 3.8+, access to analytics database, and SQL query permissions
allowed-tools: Bash Read Write Grep
---

# Funnel Query - Customer Journey Analytics

## Purpose
Standardized analytics skill for customer funnel analysis, providing common queries and insights for user journey optimization, conversion tracking, and cohort analysis across product metrics.

## When to Use
- **Conversion Analysis**: When analyzing user signup → activation → paid conversion funnels
- **Cohort Comparisons**: When comparing conversion rates between different user cohorts
- **Funnel Optimization**: When identifying drop-off points and optimization opportunities
- **Product Metrics**: When tracking key product metrics and user engagement
- **Growth Analysis**: When analyzing user growth and retention patterns
- **A/B Testing**: When measuring impact of product changes on conversion rates
- **Business Intelligence**: When generating reports for stakeholders on user journey

## Core Funnel Queries

### Standard Conversion Funnel
```sql
-- User signup → activation → paid conversion funnel
WITH funnel_stages AS (
  -- Stage 1: Signups
  SELECT 
    user_id,
    'signup' as stage,
    created_at as event_time
  FROM users 
  WHERE created_at >= '2024-01-01'
  
  UNION ALL
  
  -- Stage 2: First activation (key action)
  SELECT 
    user_id,
    'activation' as stage,
    event_time
  FROM user_events 
  WHERE event_type = 'first_key_action'
    AND created_at >= '2024-01-01'
  
  UNION ALL
  
  -- Stage 3: Paid conversion
  SELECT 
    user_id,
    'paid' as stage,
    created_at as event_time
  FROM subscriptions 
  WHERE created_at >= '2024-01-01'
),
funnel_counts AS (
  SELECT 
    stage,
    COUNT(DISTINCT user_id) as users,
    MIN(event_time) as earliest_time
  FROM funnel_stages
  GROUP BY stage
)
SELECT 
  stage,
  users,
  LAG(users) OVER (ORDER BY 
    CASE stage 
      WHEN 'signup' THEN 1 
      WHEN 'activation' THEN 2 
      WHEN 'paid' THEN 3 
    END
  ) as previous_stage_users,
  ROUND(
    users * 100.0 / LAG(users) OVER (ORDER BY 
      CASE stage 
        WHEN 'signup' THEN 1 
        WHEN 'activation' THEN 2 
        WHEN 'paid' THEN 3 
      END
    ), 2
  ) as conversion_rate
FROM funnel_counts
ORDER BY 
  CASE stage 
    WHEN 'signup' THEN 1 
    WHEN 'activation' THEN 2 
    WHEN 'paid' THEN 3 
  END;
```

### Time-to-Convert Analysis
```sql
-- Average time between funnel stages
WITH stage_times AS (
  SELECT 
    u.user_id,
    signup.created_at as signup_time,
    activation.event_time as activation_time,
    paid.created_at as paid_time
  FROM users u
  LEFT JOIN user_events activation ON u.user_id = activation.user_id 
    AND activation.event_type = 'first_key_action'
  LEFT JOIN subscriptions paid ON u.user_id = paid.user_id
  WHERE u.created_at >= '2024-01-01'
)
SELECT 
  COUNT(*) as total_users,
  AVG(DATEDIFF(activation_time, signup_time)) as avg_days_to_activate,
  AVG(DATEDIFF(paid_time, signup_time)) as avg_days_to_paid,
  AVG(DATEDIFF(paid_time, activation_time)) as avg_days_activate_to_paid
FROM stage_times
WHERE activation_time IS NOT NULL;
```

## Cohort Analysis Queries

### Monthly Cohort Retention
```sql
-- Monthly cohort retention analysis
WITH user_cohorts AS (
  SELECT 
    user_id,
    DATE_TRUNC('month', created_at) as cohort_month
  FROM users
  WHERE created_at >= '2023-01-01'
),
monthly_activity AS (
  SELECT 
    uc.user_id,
    uc.cohort_month,
    DATE_TRUNC('month', event_time) as activity_month
  FROM user_cohorts uc
  JOIN user_events ue ON uc.user_id = ue.user_id
  WHERE ue.event_time >= uc.cohort_month
    AND ue.event_time < uc.cohort_month + INTERVAL '12 months'
),
cohort_sizes AS (
  SELECT 
    cohort_month,
    COUNT(DISTINCT user_id) as cohort_size
  FROM user_cohorts
  GROUP BY cohort_month
),
retention_rates AS (
  SELECT 
    ma.cohort_month,
    ma.activity_month,
    DATEDIFF(ma.activity_month, ma.cohort_month) / 30 as period_number,
    COUNT(DISTINCT ma.user_id) as active_users,
    cs.cohort_size
  FROM monthly_activity ma
  JOIN cohort_sizes cs ON ma.cohort_month = cs.cohort_month
  GROUP BY ma.cohort_month, ma.activity_month, cs.cohort_size
)
SELECT 
  cohort_month,
  period_number,
  cohort_size,
  active_users,
  ROUND(active_users * 100.0 / cohort_size, 2) as retention_rate
FROM retention_rates
ORDER BY cohort_month, period_number;
```

### Conversion by Acquisition Channel
```sql
-- Conversion rates by marketing channel
WITH channel_attribution AS (
  SELECT 
    u.user_id,
    u.acquisition_channel,
    u.created_at as signup_date,
    CASE WHEN activation.user_id IS NOT NULL THEN 1 ELSE 0 END as activated,
    CASE WHEN paid.user_id IS NOT NULL THEN 1 ELSE 0 END as converted
  FROM users u
  LEFT JOIN (
    SELECT DISTINCT user_id 
    FROM user_events 
    WHERE event_type = 'first_key_action'
  ) activation ON u.user_id = activation.user_id
  LEFT JOIN (
    SELECT DISTINCT user_id 
    FROM subscriptions
  ) paid ON u.user_id = paid.user_id
  WHERE u.created_at >= '2024-01-01'
)
SELECT 
  acquisition_channel,
  COUNT(*) as total_signups,
  SUM(activated) as total_activated,
  SUM(converted) as total_converted,
  ROUND(SUM(activated) * 100.0 / COUNT(*), 2) as activation_rate,
  ROUND(SUM(converted) * 100.0 / COUNT(*), 2) as conversion_rate,
  ROUND(
    SUM(converted) * 100.0 / NULLIF(SUM(activated), 0), 2
  ) as activated_to_paid_rate
FROM channel_attribution
GROUP BY acquisition_channel
ORDER BY total_signups DESC;
```

## Performance Optimization Queries

### High-Volume Funnel Analysis
```sql
-- Optimized funnel query for large datasets (millions of users)
CREATE MATERIALIZED VIEW daily_funnel_metrics AS
SELECT 
  DATE(created_at) as date,
  COUNT(*) as signups,
  COUNT(DISTINCT 
    CASE WHEN EXISTS (
      SELECT 1 FROM user_events ue 
      WHERE ue.user_id = users.user_id 
        AND ue.event_type = 'first_key_action'
        AND DATE(ue.event_time) = DATE(users.created_at)
    ) THEN users.user_id END
  ) as same_day_activations,
  COUNT(DISTINCT 
    CASE WHEN EXISTS (
      SELECT 1 FROM subscriptions s 
      WHERE s.user_id = users.user_id 
        AND DATE(s.created_at) = DATE(users.created_at)
    ) THEN users.user_id END
  ) as same_day_conversions
FROM users
WHERE created_at >= '2024-01-01'
GROUP BY DATE(created_at);

-- Query the materialized view for fast results
SELECT 
  date,
  signups,
  same_day_activations,
  same_day_conversions,
  ROUND(same_day_activations * 100.0 / signups, 2) as activation_rate,
  ROUND(same_day_conversions * 100.0 / signups, 2) as conversion_rate
FROM daily_funnel_metrics
ORDER BY date DESC;
```

## Advanced Analytics

### Funnel Drop-off Analysis
```sql
-- Detailed drop-off analysis with user segments
WITH funnel_journey AS (
  SELECT 
    u.user_id,
    u.user_type, -- free, trial, enterprise
    u.acquisition_channel,
    u.created_at as signup_time,
    activation.event_time as activation_time,
    paid.event_time as paid_time,
    CASE 
      WHEN activation.event_time IS NULL THEN 'no_activation'
      WHEN paid.event_time IS NULL THEN 'no_conversion'
      ELSE 'converted'
    END as final_stage
  FROM users u
  LEFT JOIN (
    SELECT user_id, MIN(event_time) as event_time
    FROM user_events 
    WHERE event_type = 'first_key_action'
    GROUP BY user_id
  ) activation ON u.user_id = activation.user_id
  LEFT JOIN (
    SELECT user_id, MIN(created_at) as event_time
    FROM subscriptions
    GROUP BY user_id
  ) paid ON u.user_id = paid.user_id
  WHERE u.created_at >= '2024-01-01'
)
SELECT 
  final_stage,
  user_type,
  acquisition_channel,
  COUNT(*) as user_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY final_stage), 2) as stage_percentage
FROM funnel_journey
GROUP BY final_stage, user_type, acquisition_channel
ORDER BY final_stage, stage_percentage DESC;
```

### Predictive Conversion Indicators
```sql
-- Early indicators of likely conversion
WITH user_behavior AS (
  SELECT 
    u.user_id,
    u.created_at as signup_time,
    -- Early engagement metrics
    COUNT(DISTINCT DATE(ue.event_time)) as active_days_first_week,
    COUNT(DISTINCT ue.event_type) as unique_actions_first_week,
    MAX(ue.event_time) as last_activity,
    -- Product usage depth
    COUNT(DISTINCT ue.feature_used) as features_used_first_week,
    CASE WHEN s.user_id IS NOT NULL THEN 1 ELSE 0 END as converted
  FROM users u
  LEFT JOIN user_events ue ON u.user_id = ue.user_id 
    AND ue.event_time BETWEEN u.created_at AND u.created_at + INTERVAL '7 days'
  LEFT JOIN subscriptions s ON u.user_id = s.user_id
  WHERE u.created_at >= '2024-01-01'
    AND u.created_at < '2024-02-01' -- Limit to complete month
  GROUP BY u.user_id, u.created_at
)
SELECT 
  converted,
  AVG(active_days_first_week) as avg_active_days,
  AVG(unique_actions_first_week) as avg_unique_actions,
  AVG(features_used_first_week) as avg_features_used,
  COUNT(*) as user_count
FROM user_behavior
GROUP BY converted
ORDER BY converted;
```

## Gotchas

### Common Pitfalls
- **Time Zone Issues**: Always standardize timestamps to UTC for consistent analysis
- **Data Freshness**: Real-time analytics may have delays in data ingestion
- **User Identification**: Ensure consistent user ID handling across different data sources
- **Sample Bias**: Be aware of selection bias when analyzing specific user segments

### Edge Cases
- **Multiple Conversions**: Users may convert multiple times (e.g., trial → paid → enterprise)
- **Cross-Device Users**: Single users may have multiple device IDs or sessions
- **Data Gaps**: Missing events due to tracking failures or system outages
- **Seasonal Effects**: Account for seasonal patterns in conversion rates

### Performance Issues
- **Query Complexity**: Complex funnel queries can be slow on large datasets
- **Join Optimization**: Use appropriate indexing and query optimization strategies
- **Memory Usage**: Large result sets can consume significant memory
- **Concurrent Queries**: Multiple analysts running complex queries can impact database performance

### Security Considerations
- **PII Protection**: User data may contain personally identifiable information
- **Data Access**: Implement proper access controls for sensitive analytics data
- **Audit Requirements**: Track who accesses what data and when
- **Data Retention**: Follow data retention policies for user analytics data

### Troubleshooting
- **Missing Events**: Check event tracking implementation and data pipelines
- **Inconsistent Counts**: Verify user ID consistency across data sources
- **Time Zone Conflicts**: Ensure all timestamps use consistent time zones
- **Query Timeouts**: Optimize queries or use materialized views for frequently accessed data

## Integration Examples

### Python Integration
```python
import pandas as pd
from sqlalchemy import create_engine

class FunnelAnalyzer:
    def __init__(self, db_connection_string):
        self.engine = create_engine(db_connection_string)
    
    def get_conversion_funnel(self, start_date, end_date):
        query = """
        WITH funnel_stages AS (
          SELECT user_id, 'signup' as stage, created_at as event_time
          FROM users WHERE created_at >= %s AND created_at < %s
          UNION ALL
          SELECT user_id, 'activation' as stage, event_time
          FROM user_events WHERE event_type = 'first_key_action'
            AND event_time >= %s AND event_time < %s
          UNION ALL
          SELECT user_id, 'paid' as stage, created_at as event_time
          FROM subscriptions WHERE created_at >= %s AND created_at < %s
        )
        SELECT stage, COUNT(DISTINCT user_id) as users
        FROM funnel_stages
        GROUP BY stage
        ORDER BY 
          CASE stage WHEN 'signup' THEN 1 WHEN 'activation' THEN 2 WHEN 'paid' THEN 3 END
        """
        
        df = pd.read_sql(query, self.engine, params=[start_date, end_date] * 3)
        return df
    
    def calculate_conversion_rates(self, funnel_df):
        funnel_df['previous_users'] = funnel_df['users'].shift(1)
        funnel_df['conversion_rate'] = (
            funnel_df['users'] / funnel_df['previous_users'] * 100
        ).round(2)
        return funnel_df
```

### Dashboard Integration
```python
# Example: Daily funnel metrics for dashboard
def get_daily_funnel_metrics():
    query = """
    SELECT 
      DATE(created_at) as date,
      COUNT(*) as signups,
      COUNT(DISTINCT CASE WHEN activated.user_id IS NOT NULL THEN users.user_id END) as activations,
      COUNT(DISTINCT CASE WHEN paid.user_id IS NOT NULL THEN users.user_id END) as conversions
    FROM users
    LEFT JOIN (
      SELECT DISTINCT user_id, MIN(event_time) as activation_time
      FROM user_events WHERE event_type = 'first_key_action'
      GROUP BY user_id
    ) activated ON users.user_id = activated.user_id 
      AND DATE(activated.activation_time) = DATE(users.created_at)
    LEFT JOIN (
      SELECT DISTINCT user_id, MIN(created_at) as paid_time
      FROM subscriptions GROUP BY user_id
    ) paid ON users.user_id = paid.user_id 
      AND DATE(paid.paid_time) = DATE(users.created_at)
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY DATE(created_at)
    ORDER BY date DESC
    """
    return pd.read_sql(query, engine)
```

## Configuration

### Database Connection
```python
# config.py
ANALYTICS_DB_CONFIG = {
    'host': 'analytics-db.internal.company.com',
    'port': 5432,
    'database': 'product_analytics',
    'username': 'analytics_user',
    'password': os.getenv('ANALYTICS_DB_PASSWORD'),
    'sslmode': 'require'
}

# Query timeout settings
QUERY_TIMEOUT = 300  # 5 minutes
MAX_RESULT_ROWS = 100000  # Limit result size for performance
```

## References

Load these files when needed:
- `scripts/funnel-analyzer.py` - Core funnel analysis and reporting tools
- `scripts/cohort-calculator.py` - Cohort analysis and retention calculations
- `references/analytics-schema.md` - Complete database schema documentation
- `assets/query-templates.sql` - Reusable SQL query templates
- `examples/dashboard-queries/` - Sample queries for common dashboard widgets
