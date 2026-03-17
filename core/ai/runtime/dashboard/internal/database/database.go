package database

import (
	"database/sql"
	"fmt"

	_ "github.com/lib/pq"
)

func NewConnection(databaseURL string) (*sql.DB, error) {
	db, err := sql.Open("postgres", databaseURL)
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    language VARCHAR(50) NOT NULL,   -- rust, go, python
    backend VARCHAR(50) NOT NULL,    -- llama-cpp, ollama
    status VARCHAR(50) NOT NULL DEFAULT 'idle',
    skills JSONB DEFAULT '[]',
    last_activity TIMESTAMP WITH TIME ZONE,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_language ON agents(language);
`

const createSkillsTable = `
CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(64) NOT NULL UNIQUE,    -- agentskills.io: max 64 chars, lowercase
    description TEXT NOT NULL,           -- agentskills.io: required
    license VARCHAR(255),                -- agentskills.io: optional
    compatibility VARCHAR(500),          -- agentskills.io: optional, max 500 chars
    metadata JSONB DEFAULT '{}',         -- project keys: risk_level, autonomy, layer, human_gate
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name);
CREATE INDEX IF NOT EXISTS idx_skills_metadata ON skills USING GIN(metadata);
`

const createActivitiesTable = `
CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL,
    agent_id UUID REFERENCES agents(id),
    agent_name VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_activities_agent_id ON activities(agent_id);
CREATE INDEX IF NOT EXISTS idx_activities_type ON activities(type);
`

const createAgentExecutionsTable = `
CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id),
    skill_name VARCHAR(64) REFERENCES skills(name),
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_id ON agent_executions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_skill_name ON agent_executions(skill_name);
CREATE INDEX IF NOT EXISTS idx_agent_executions_status ON agent_executions(status);
CREATE INDEX IF NOT EXISTS idx_agent_executions_started_at ON agent_executions(started_at DESC);
`
