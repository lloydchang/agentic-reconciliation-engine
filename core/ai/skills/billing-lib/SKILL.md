---
name: billing-lib
description: Use when working with the internal billing library for cost allocation, invoice processing, or revenue recognition. Documents API usage, data models, common patterns, and integration methods for billing operations across services.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "1.0"
  category: library-reference
  risk_level: low
  autonomy: fully_auto
  layer: temporal
compatibility: Requires Python 3.8+, access to billing database, and billing library installation
allowed-tools: Bash Read Write Grep
---

# Internal Billing Library Reference

## Purpose
Comprehensive reference for the internal billing library, documenting API usage, data models, integration patterns, and common operations for cost allocation and revenue recognition.

## When to Use
- **Cost Allocation**: When allocating costs to different departments, projects, or customers
- **Invoice Processing**: When generating or processing invoices and billing statements
- **Revenue Recognition**: When implementing revenue recognition logic and reporting
- **Usage Tracking**: When tracking service usage for billing purposes
- **Price Calculation**: When calculating prices based on usage tiers, discounts, or custom pricing
- **Integration Development**: When integrating new services with the billing system
- **Reporting**: When generating billing reports and financial analytics

## Library Overview

### Core Components

#### BillingClient
Main client for interacting with the billing system:
```python
from billing_lib import BillingClient

client = BillingClient(
    api_url="https://billing.internal.company.com",
    api_key="your-api-key",
    timeout=30
)
```

#### UsageTracker
Tracks and aggregates service usage:
```python
from billing_lib import UsageTracker

tracker = UsageTracker(client)
usage = tracker.get_usage(
    service_id="web-api",
    customer_id="cust-123",
    period="2024-01"
)
```

#### PriceCalculator
Calculates costs based on usage and pricing rules:
```python
from billing_lib import PriceCalculator

calculator = PriceCalculator()
cost = calculator.calculate_cost(
    usage_record=usage,
    pricing_tier="enterprise"
)
```

## API Reference

### Customer Management

#### Create Customer
```python
customer = client.create_customer(
    name="Acme Corp",
    billing_email="billing@acme.com",
    address={
        "street": "123 Business St",
        "city": "San Francisco",
        "state": "CA",
        "zip": "94105",
        "country": "US"
    },
    metadata={"industry": "technology", "size": "enterprise"}
)
```

#### Get Customer
```python
customer = client.get_customer(customer_id="cust-123")
```

#### Update Customer
```python
customer = client.update_customer(
    customer_id="cust-123",
    billing_email="new-billing@acme.com"
)
```

### Usage Tracking

#### Record Usage
```python
usage_record = tracker.record_usage(
    service_id="web-api",
    customer_id="cust-123",
    usage_type="api_calls",
    quantity=1000,
    unit="calls",
    timestamp="2024-01-15T10:00:00Z",
    metadata={"endpoint": "/api/v1/users"}
)
```

#### Get Usage Summary
```python
summary = tracker.get_usage_summary(
    customer_id="cust-123",
    start_date="2024-01-01",
    end_date="2024-01-31",
    group_by=["service_id", "usage_type"]
)
```

### Invoice Generation

#### Generate Invoice
```python
invoice = client.generate_invoice(
    customer_id="cust-123",
    period="2024-01",
    due_date="2024-02-15",
    line_items=[
        {
            "description": "API Usage",
            "quantity": 100000,
            "unit_price": 0.001,
            "total": 100.00
        }
    ]
)
```

#### Get Invoice
```python
invoice = client.get_invoice(invoice_id="inv-456")
```

## Data Models

### Customer
```python
@dataclass
class Customer:
    id: str
    name: str
    billing_email: str
    address: Address
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    status: CustomerStatus  # ACTIVE, SUSPENDED, CANCELLED
```

### UsageRecord
```python
@dataclass
class UsageRecord:
    id: str
    service_id: str
    customer_id: str
    usage_type: str
    quantity: Decimal
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any]
```

### Invoice
```python
@dataclass
class Invoice:
    id: str
    customer_id: str
    period: str
    status: InvoiceStatus  # DRAFT, SENT, PAID, OVERDUE
    total_amount: Decimal
    due_date: date
    line_items: List[LineItem]
    created_at: datetime
```

## Gotchas

### Common Pitfalls
- **Decimal Precision**: Always use Decimal for monetary calculations, never float
- **Time Zone Handling**: Usage timestamps must be in UTC for consistent reporting
- **Idempotency**: Usage recording should be idempotent to handle retries
- **Rate Limiting**: Billing API has rate limits, implement exponential backoff

### Edge Cases
- **Free Tiers**: Handle free tier usage correctly to avoid billing errors
- **Prorated Billing**: Mid-month customer changes require prorated calculations
- **Currency Conversion**: Multi-currency billing requires real-time exchange rates
- **Tax Calculation**: Tax rules vary by jurisdiction and customer location

### Performance Issues
- **Large Usage Volumes**: High-volume services may need batch processing
- **Database Queries**: Complex reporting queries can be slow, optimize indexes
- **Memory Usage**: Loading large customer datasets can consume significant memory
- **API Timeouts**: Long-running calculations may hit API timeouts

### Security Considerations
- **PII Protection**: Customer billing information contains sensitive PII
- **Access Control**: Billing operations require proper authorization
- **Audit Trail**: All billing changes must be logged for compliance
- **Data Encryption**: Billing data should be encrypted at rest and in transit

### Troubleshooting
- **Duplicate Usage**: Check for duplicate usage records causing over-billing
- **Missing Invoices**: Verify usage data is complete before invoice generation
- **Calculation Errors**: Validate pricing rules and tax calculations regularly
- **Integration Failures**: Monitor external system integrations for billing data

## Integration Patterns

### Service Integration
```python
# Example: Integrating a new service
from billing_lib import UsageTracker, BillingClient

class MyServiceBilling:
    def __init__(self):
        self.client = BillingClient.from_config()
        self.tracker = UsageTracker(self.client)
    
    def track_api_usage(self, customer_id, endpoint, count):
        return self.tracker.record_usage(
            service_id="my-service",
            customer_id=customer_id,
            usage_type="api_calls",
            quantity=count,
            unit="calls",
            metadata={"endpoint": endpoint}
        )
```

### Batch Processing
```python
# Example: Processing usage in batches
def process_daily_usage():
    tracker = UsageTracker(BillingClient.from_config())
    
    # Get usage from monitoring system
    usage_data = get_usage_from_monitoring("2024-01-15")
    
    # Batch record usage
    batch_results = []
    for record in usage_data:
        try:
            result = tracker.record_usage(**record)
            batch_results.append(result)
        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
    
    return batch_results
```

## Configuration

### Environment Variables
```bash
BILLING_API_URL=https://billing.internal.company.com
BILLING_API_KEY=your-api-key
BILLING_TIMEOUT=30
BILLING_RETRY_ATTEMPTS=3
BILLING_BATCH_SIZE=100
```

### Configuration File
```yaml
billing:
  api_url: "https://billing.internal.company.com"
  api_key: "${BILLING_API_KEY}"
  timeout: 30
  retry_attempts: 3
  batch_size: 100
  
pricing:
  default_currency: "USD"
  tax_inclusive: false
  
reporting:
  timezone: "UTC"
  fiscal_month_start_day: 1
```

## Testing

### Unit Tests
```python
import pytest
from billing_lib import BillingClient, UsageTracker
from unittest.mock import Mock, patch

class TestBillingClient:
    @pytest.fixture
    def client(self):
        return BillingClient(
            api_url="https://test.billing.com",
            api_key="test-key"
        )
    
    def test_create_customer(self, client):
        with patch.object(client, 'post') as mock_post:
            mock_post.return_value.json.return_value = {
                "id": "cust-123",
                "name": "Test Customer"
            }
            
            customer = client.create_customer(name="Test Customer")
            
            assert customer.id == "cust-123"
            assert customer.name == "Test Customer"
```

### Integration Tests
```python
class TestBillingIntegration:
    def test_end_to_end_billing(self):
        # Setup test customer
        customer = client.create_customer(
            name="Test Customer",
            billing_email="test@example.com"
        )
        
        # Record usage
        usage = tracker.record_usage(
            service_id="test-service",
            customer_id=customer.id,
            usage_type="api_calls",
            quantity=100
        )
        
        # Generate invoice
        invoice = client.generate_invoice(
            customer_id=customer.id,
            period="2024-01"
        )
        
        assert invoice.total_amount > 0
        assert len(invoice.line_items) > 0
```

## References

Load these files when needed:
- `scripts/billing-integration.py` - Integration helpers and utilities
- `scripts/usage-aggregator.py` - Usage data aggregation and processing
- `references/billing-api-spec.md` - Complete API specification
- `assets/pricing-rules.yaml` - Pricing rule definitions and examples
- `examples/integration-patterns/` - Service integration examples and patterns
