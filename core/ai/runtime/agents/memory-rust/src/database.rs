use sqlx::{migrate::MigrateDatabase, SqlitePool};
use anyhow::Result;

pub async fn initialize_database(database_url: &str) -> Result<SqlitePool> {
    // Create database if it doesn't exist
    if !SqlitePool::connect(database_url).await.is_ok() {
        sqlx::Sqlite::create_database(database_url).await?;
    }

    let pool = SqlitePool::connect(database_url).await?;

    // Run migrations
    create_tables(&pool).await?;

    Ok(pool)
}

async fn create_tables(pool: &SqlitePool) -> Result<()> {
    // Episodes table - conversation history
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS episodes (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        "#,
    )
    .execute(pool)
    .await?;

    // Semantic table - learned concepts and relationships
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS semantic_memory (
            id TEXT PRIMARY KEY,
            concept TEXT NOT NULL,
            definition TEXT,
            relationships TEXT,
            confidence REAL DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        "#,
    )
    .execute(pool)
    .await?;

    // Procedural table - skill execution patterns
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS procedural_memory (
            id TEXT PRIMARY KEY,
            skill_name TEXT NOT NULL,
            pattern TEXT NOT NULL,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            last_used DATETIME,
            effectiveness_score REAL DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        "#,
    )
    .execute(pool)
    .await?;

    // Working table - current session context
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS working_memory (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            context_key TEXT NOT NULL,
            context_value TEXT NOT NULL,
            expires_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        "#,
    )
    .execute(pool)
    .await?;

    // Events table - for Argo Events integration
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            source TEXT NOT NULL,
            namespace TEXT,
            component TEXT,
            severity TEXT,
            description TEXT,
            payload TEXT,
            correlation_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            processed_at DATETIME
        )
        "#,
    )
    .execute(pool)
    .await?;

    // Workflows table - Temporal workflow tracking
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            workflow_type TEXT NOT NULL,
            skill_name TEXT,
            status TEXT DEFAULT 'pending',
            input_data TEXT,
            output_data TEXT,
            error_message TEXT,
            execution_time_ms INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            started_at DATETIME,
            completed_at DATETIME
        )
        "#,
    )
    .execute(pool)
    .await?;

    // Incidents table - for tracking escalations and resolutions
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            severity TEXT,
            status TEXT DEFAULT 'open',
            component TEXT,
            namespace TEXT,
            resolution TEXT,
            rollback_actions TEXT,
            lessons_learned TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME
        )
        "#,
    )
    .execute(pool)
    .await?;

    // Create indexes for better performance
    let indexes = vec![
        "CREATE INDEX IF NOT EXISTS idx_episodes_session_id ON episodes(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_events_correlation_id ON events(correlation_id)",
        "CREATE INDEX IF NOT EXISTS idx_events_status ON events(status)",
        "CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status)",
        "CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)",
        "CREATE INDEX IF NOT EXISTS idx_working_memory_session_id ON working_memory(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_procedural_memory_skill_name ON procedural_memory(skill_name)",
    ];

    for index in indexes {
        sqlx::query(index).execute(pool).await?;
    }

    Ok(())
}
