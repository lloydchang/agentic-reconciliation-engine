package database

import (
	"database/sql"
	"fmt"

	_ "github.com/lib/pq"
	_ "github.com/mattn/go-sqlite3"
)

func NewConnection(databaseURL string) (*sql.DB, error) {
	// Support both PostgreSQL and SQLite
	driver := "postgres"
	if len(databaseURL) > 7 && databaseURL[:7] == "sqlite:" {
		driver = "sqlite3"
		// For SQLite, the connection string should just be the file path
		databaseURL = databaseURL[7:] // Remove "sqlite:" prefix
	} else if len(databaseURL) > 0 && databaseURL[0] == '/' {
		// Direct file path for SQLite
		driver = "sqlite3"
	}
	
	db, err := sql.Open(driver, databaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to open database connection: %w", err)
	}

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return db, nil
}

func RunMigrations(db *sql.DB) error {
	migrations := []string{
		createAgentsTable,
		createSkillsTable,
		createActivitiesTable,
		createAgentExecutionsTable,
	}

	for _, migration := range migrations {
		if _, err := db.Exec(migration); err != nil {
			return fmt.Errorf("migration failed: %w", err)
		}
	}

	return nil
}

const createAgentsTable = `
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL,
    language TEXT NOT NULL,   -- rust, go, python
    backend TEXT NOT NULL,    -- llama-cpp, ollama
    status TEXT NOT NULL DEFAULT 'idle',
    skills TEXT DEFAULT '[]',
    last_activity DATETIME,
    success_rate REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_language ON agents(language);
`

const createSkillsTable = `
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL UNIQUE,    -- agentskills.io: max 64 chars, lowercase
    description TEXT NOT NULL,           -- agentskills.io: required
    license TEXT,                -- agentskills.io: optional
    compatibility TEXT,          -- agentskills.io: optional, max 500 chars
    metadata TEXT DEFAULT '{}',         -- project keys: risk_level, autonomy, layer, human_gate
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name);
`

const createActivitiesTable = `
CREATE TABLE IF NOT EXISTS activities (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    type TEXT NOT NULL,
    agent_id TEXT REFERENCES agents(id),
    agent_name TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_activities_agent_id ON activities(agent_id);
CREATE INDEX IF NOT EXISTS idx_activities_type ON activities(type);
`

const createAgentExecutionsTable = `
CREATE TABLE IF NOT EXISTS agent_executions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    agent_id TEXT REFERENCES agents(id),
    skill_name TEXT REFERENCES skills(name),
    status TEXT NOT NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    result TEXT,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_id ON agent_executions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_skill_name ON agent_executions(skill_name);
CREATE INDEX IF NOT EXISTS idx_agent_executions_status ON agent_executions(status);
CREATE INDEX IF NOT EXISTS idx_agent_executions_started_at ON agent_executions(started_at DESC);
`
