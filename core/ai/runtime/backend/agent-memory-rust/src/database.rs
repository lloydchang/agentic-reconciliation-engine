use crate::{
    error::Result,
    models::{Conversation, Message, KnowledgeBase, AgentState, MessageRole},
};
use chrono::Utc;
use rusqlite::{Connection, params, Row};
use std::path::Path;

/// Database manager for agent memory
pub struct Database {
    connection: Connection,
}

impl Database {
    pub fn new<P: AsRef<Path>>(path: P) -> Result<Self> {
        let connection = Connection::open(path)?;
        let db = Self { connection };
        db.initialize()?;
        Ok(db)
    }

    fn initialize(&self) -> Result<()> {
        // Create tables
        self.connection.execute(
            r#"
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at DATETIME,
                updated_at DATETIME,
                metadata TEXT
            )
            "#,
            [],
        )?;

        self.connection.execute(
            r#"
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                timestamp DATETIME,
                metadata TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
            "#,
            [],
        )?;

        self.connection.execute(
            r#"
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                embedding BLOB,
                created_at DATETIME,
                updated_at DATETIME,
                tags TEXT
            )
            "#,
            [],
        )?;

        self.connection.execute(
            r#"
            CREATE TABLE IF NOT EXISTS agent_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME
            )
            "#,
            [],
        )?;

        // Create indexes
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)",
            [],
        )?;

        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)",
            [],
        )?;

        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge_base(tags)",
            [],
        )?;

        Ok(())
    }

    // Conversation operations
    pub fn create_conversation(&self, conversation: &Conversation) -> Result<()> {
        self.connection.execute(
            r#"
            INSERT INTO conversations (id, title, created_at, updated_at, metadata)
            VALUES (?1, ?2, ?3, ?4, ?5)
            "#,
            params![
                conversation.id,
                conversation.title,
                conversation.created_at,
                conversation.updated_at,
                conversation.metadata.map(|m| serde_json::to_string(m)).transpose()?,
            ],
        )?;
        Ok(())
    }

    pub fn get_conversation(&self, id: &str) -> Result<Option<Conversation>> {
        let mut stmt = self.connection.prepare(
            r#"
            SELECT id, title, created_at, updated_at, metadata
            FROM conversations
            WHERE id = ?1
            "#,
        )?;

        let mut rows = stmt.query([id])?;
        
        if let Some(row) = rows.next()? {
            Ok(Some(Conversation {
                id: row.get(0)?,
                title: row.get(1)?,
                created_at: row.get(2)?,
                updated_at: row.get(3)?,
                metadata: row.get::<_, Option<String>>(4)?
                    .map(|s| serde_json::from_str(&s))
                    .transpose()?,
            }))
        } else {
            Ok(None)
        }
    }

    pub fn list_conversations(&self, limit: Option<u32>) -> Result<Vec<Conversation>> {
        let sql = if let Some(limit) = limit {
            format!("SELECT id, title, created_at, updated_at, metadata FROM conversations ORDER BY updated_at DESC LIMIT {}", limit)
        } else {
            "SELECT id, title, created_at, updated_at, metadata FROM conversations ORDER BY updated_at DESC".to_string()
        };

        let mut stmt = self.connection.prepare(&sql)?;
        let mut rows = stmt.query([])?;
        
        let mut conversations = Vec::new();
        while let Some(row) = rows.next()? {
            conversations.push(Conversation {
                id: row.get(0)?,
                title: row.get(1)?,
                created_at: row.get(2)?,
                updated_at: row.get(3)?,
                metadata: row.get::<_, Option<String>>(4)?
                    .map(|s| serde_json::from_str(&s))
                    .transpose()?,
            });
        }
        
        Ok(conversations)
    }

    pub fn update_conversation(&self, conversation: &Conversation) -> Result<()> {
        self.connection.execute(
            r#"
            UPDATE conversations
            SET title = ?2, updated_at = ?3, metadata = ?4
            WHERE id = ?1
            "#,
            params![
                conversation.id,
                conversation.title,
                conversation.updated_at,
                conversation.metadata.map(|m| serde_json::to_string(m)).transpose()?,
            ],
        )?;
        Ok(())
    }

    pub fn delete_conversation(&self, id: &str) -> Result<()> {
        self.connection.execute("DELETE FROM messages WHERE conversation_id = ?1", [id])?;
        self.connection.execute("DELETE FROM conversations WHERE id = ?1", [id])?;
        Ok(())
    }

    // Message operations
    pub fn create_message(&self, message: &Message) -> Result<()> {
        self.connection.execute(
            r#"
            INSERT INTO messages (id, conversation_id, role, content, timestamp, metadata)
            VALUES (?1, ?2, ?3, ?4, ?5, ?6)
            "#,
            params![
                message.id,
                message.conversation_id,
                serde_json::to_string(&message.role)?,
                message.content,
                message.timestamp,
                message.metadata.map(|m| serde_json::to_string(m)).transpose()?,
            ],
        )?;
        Ok(())
    }

    pub fn get_messages(&self, conversation_id: &str, limit: Option<u32>) -> Result<Vec<Message>> {
        let sql = if let Some(limit) = limit {
            format!(
                "SELECT id, conversation_id, role, content, timestamp, metadata FROM messages WHERE conversation_id = ?1 ORDER BY timestamp ASC LIMIT {}",
                limit
            )
        } else {
            "SELECT id, conversation_id, role, content, timestamp, metadata FROM messages WHERE conversation_id = ?1 ORDER BY timestamp ASC".to_string()
        };

        let mut stmt = self.connection.prepare(&sql)?;
        let mut rows = stmt.query([conversation_id])?;
        
        let mut messages = Vec::new();
        while let Some(row) = rows.next()? {
            messages.push(Message {
                id: row.get(0)?,
                conversation_id: row.get(1)?,
                role: serde_json::from_str(&row.get::<_, String>(2)?)?,
                content: row.get(3)?,
                timestamp: row.get(4)?,
                metadata: row.get::<_, Option<String>>(5)?
                    .map(|s| serde_json::from_str(&s))
                    .transpose()?,
            });
        }
        
        Ok(messages)
    }

    // Knowledge base operations
    pub fn create_knowledge(&self, knowledge: &KnowledgeBase) -> Result<()> {
        self.connection.execute(
            r#"
            INSERT INTO knowledge_base (id, title, content, embedding, created_at, updated_at, tags)
            VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)
            "#,
            params![
                knowledge.id,
                knowledge.title,
                knowledge.content,
                knowledge.embedding.as_ref().map(|e| serde_json::to_vec(e)).transpose()?,
                knowledge.created_at,
                knowledge.updated_at,
                serde_json::to_string(&knowledge.tags)?,
            ],
        )?;
        Ok(())
    }

    pub fn search_knowledge(&self, query: &str, limit: u32) -> Result<Vec<KnowledgeBase>> {
        let mut stmt = self.connection.prepare(
            r#"
            SELECT id, title, content, embedding, created_at, updated_at, tags
            FROM knowledge_base
            WHERE content LIKE ?1 OR title LIKE ?1
            ORDER BY updated_at DESC
            LIMIT ?2
            "#,
        )?;

        let mut rows = stmt.query([format!("%{}%", query), limit.to_string()])?;
        
        let mut results = Vec::new();
        while let Some(row) = rows.next()? {
            results.push(KnowledgeBase {
                id: row.get(0)?,
                title: row.get(1)?,
                content: row.get(2)?,
                embedding: row.get::<_, Option<Vec<u8>>>(3)?
                    .map(|e| serde_json::from_slice(&e))
                    .transpose()?,
                created_at: row.get(4)?,
                updated_at: row.get(5)?,
                tags: serde_json::from_str(&row.get::<_, String>(6)?)?,
            });
        }
        
        Ok(results)
    }

    // Agent state operations
    pub fn set_state(&self, key: &str, value: &str) -> Result<()> {
        let now = Utc::now();
        self.connection.execute(
            r#"
            INSERT OR REPLACE INTO agent_state (key, value, updated_at)
            VALUES (?1, ?2, ?3)
            "#,
            params![key, value, now],
        )?;
        Ok(())
    }

    pub fn get_state(&self, key: &str) -> Result<Option<String>> {
        let mut stmt = self.connection.prepare("SELECT value FROM agent_state WHERE key = ?1")?;
        let mut rows = stmt.query([key])?;
        
        if let Some(row) = rows.next()? {
            Ok(Some(row.get(0)?))
        } else {
            Ok(None)
        }
    }

    pub fn list_states(&self) -> Result<Vec<AgentState>> {
        let mut stmt = self.connection.prepare("SELECT key, value, updated_at FROM agent_state ORDER BY updated_at DESC")?;
        let mut rows = stmt.query([])?;
        
        let mut states = Vec::new();
        while let Some(row) = rows.next()? {
            states.push(AgentState {
                key: row.get(0)?,
                value: row.get(1)?,
                updated_at: row.get(2)?,
            });
        }
        
        Ok(states)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_database_initialization() -> Result<()> {
        let dir = tempdir()?;
        let db_path = dir.path().join("test.db");
        let db = Database::new(db_path)?;
        
        // Should not error
        Ok(())
    }

    #[test]
    fn test_conversation_operations() -> Result<()> {
        let dir = tempdir()?;
        let db_path = dir.path().join("test.db");
        let db = Database::new(db_path)?;
        
        let conv = Conversation::new(Some("Test Conversation".to_string()));
        db.create_conversation(&conv)?;
        
        let retrieved = db.get_conversation(&conv.id)?;
        assert!(retrieved.is_some());
        assert_eq!(retrieved.unwrap().title, Some("Test Conversation".to_string()));
        
        Ok(())
    }

    #[test]
    fn test_message_operations() -> Result<()> {
        let dir = tempdir()?;
        let db_path = dir.path().join("test.db");
        let db = Database::new(db_path)?;
        
        let conv = Conversation::new(None);
        db.create_conversation(&conv)?;
        
        let msg = Message::new(conv.id.clone(), MessageRole::User, "Hello".to_string());
        db.create_message(&msg)?;
        
        let messages = db.get_messages(&conv.id, None)?;
        assert_eq!(messages.len(), 1);
        assert_eq!(messages[0].content, "Hello");
        
        Ok(())
    }
}
