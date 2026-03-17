# RAG + Qwen Integration Plan

## Overview

This document outlines the integration of Retrieval-Augmented Generation (RAG) with our existing Qwen + llama.cpp setup in the GitOps control plane dashboard.

## ✅ Existing Infrastructure Confirmed

Based on the codebase analysis, you have:

### ✅ **Qwen Model Setup**
- **Model**: `qwen2.5:0.5b` (ultra-lightweight, optimized for cost)
- **Deployment**: Both llama.cpp and Ollama support
- **Backend Priority**: `llama.cpp,ollama` (prefers in-process llama.cpp)
- **Model Path**: `/models/qwen2.5-0.5b.gguf`

### ✅ **Inference Architecture**
- **Primary**: llama.cpp (in-process, faster performance)
- **Fallback**: Ollama service at `http://ollama-service:11434`
- **Multi-language**: Rust, Go, Python agents
- **API Endpoints**: Already available for inference

### ✅ **Data Infrastructure**
- **SQLite**: Agent memory (10Gi PVC) - conversation history, episodic memory
- **PostgreSQL**: Dashboard state - operational data, metrics
- **Temporal**: Workflow execution history
- **Kubernetes API**: Live cluster state
- **Dashboard APIs**: Real-time metrics and agent status

### ✅ **Current Deployment Configuration**
```yaml
# Environment variables already configured
OLLAMA_MODEL="qwen2.5:0.5b"
BACKEND_PRIORITY="llama.cpp,ollama"
MODEL_PATH="/models/qwen2.5-0.5b.gguf"
TEMPORAL_ADDRESS="temporal-frontend.ai-infrastructure.svc.cluster.local:7233"
DATABASE_URL="postgres://dashboard_user:password@postgres:5432/ai_agents_dashboard"
```

## Current Infrastructure Assessment

### ✅ What We Already Have

**1. Qwen + llama.cpp Setup**
- Qwen model running via llama.cpp
- Existing API endpoints for inference
- Self-hosted, no external dependencies

**2. Dashboard Backend (Go)**
- PostgreSQL database for dashboard state
- Existing API infrastructure
- Kubernetes deployment manifests

**3. Data Sources Available**
- **SQLite (10Gi PVC)**: Agent memory, conversation history, inference state
- **PostgreSQL**: Dashboard operational state, execution history
- **Temporal**: Workflow execution history, skill outcomes  
- **Kubernetes API**: Cluster state, resource status, events
- **Dashboard APIs**: Agent status, skill execution, system metrics
- **File System**: AGENTS.md, skills docs, configuration files

**4. Frontend (React TypeScript)**
- Existing dashboard UI
- Real-time updates via WebSocket
- Component architecture ready for expansion

### 🔄 What Needs to Be Added

**1. Vector Storage**
- pgvector extension to existing PostgreSQL
- Document embedding storage
- Similarity search indexes

**2. RAG Orchestration Layer**
- Query analysis to determine data sources
- Context building from multiple sources
- RAG-enhanced prompt engineering

**3. Data Source Connectors**
- SQLite agent memory connector
- Kubernetes API connector
- Temporal workflow connector
- File system documentation indexer

## Implementation Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Dashboard Frontend                       │
│                   (React + TypeScript)                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Qwen RAG Chat Component                │   │
│  │  - Source selection                                │   │
│  │  - Message history                                  │   │
│  │  - Real-time responses                              │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP/WebSocket
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                Dashboard Backend (Go)                       │
│                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   RAG       │ │   Data      │ │     Qwen                 │ │
│  │  Service    │ │ Connectors  │ │   Interface              │ │
│  │             │ │             │ │ (llama.cpp)              │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└───────────┬───────────────────┬───────────────────────────────┘
            │                   │
            ▼                   ▼
┌───────────────────────┐  ┌───────────────────────────────────┐
│   Data Source Layer    │  │       PostgreSQL + pgvector        │
│                        │  │                                     │
│ ┌─────────────────────┐│  │ ┌─────────────────────────────────┐ │
│ │ SQLite (Agent Mem) ││  │ │ Dashboard State                 │ │
│ │ Kubernetes API     ││  │ │ Document Embeddings              │ │
│ │ Temporal Workflows  ││  │ │ Vector Search Index             │ │
│ │ File System Docs    ││  │ └─────────────────────────────────┘ │
│ │ Dashboard APIs      ││  │                                     │
│ └─────────────────────┘│  │ ┌─────────────────────────────────┐ │
│                        │  │ │ RAG Documents Table              │ │
└───────────────────────┘  │ │ (content, embedding, source)     │ │
                           │ └─────────────────────────────────┘ │
                           └───────────────────────────────────┘
            │                          │
            └──────────────┬───────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Qwen + llama.cpp                          │
│                 (Existing Infrastructure)                    │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Database Setup (30 minutes)

**1. Add pgvector to PostgreSQL**
```sql
-- Connect to existing dashboard database
CREATE EXTENSION IF NOT EXISTS vector;

-- RAG documents table
CREATE TABLE rag_documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Vector similarity index
CREATE INDEX ON rag_documents USING ivfflat (embedding vector_cosine_ops);
```

**2. Update Dashboard Configuration**
```yaml
# core/ai/runtime/dashboard/deployment/kubernetes/dashboard-deployment.yaml
env:
- name: RAG_ENABLED
  value: "true"
- name: PGVECTOR_ENABLED
  value: "true"
- name: QWEN_LLAMACPP_URL
  value: "http://your-existing-llamacpp:8080"
```

### Phase 2: Backend RAG Service (2 hours)

**1. Qwen Client Integration**
```go
// pkg/rag/qwen_client.go
type QwenClient struct {
    llamaURL string
    client   *http.Client
}

func NewQwenClient(llamaURL string) *QwenClient {
    return &QwenClient{
        llamaURL: llamaURL,
        client:   &http.Client{Timeout: 30 * time.Second},
    }
}

func (q *QwenClient) Generate(ctx context.Context, prompt string, context []Document) (*LLMResponse, error) {
    ragPrompt := q.buildRAGPrompt(prompt, context)
    
    payload := map[string]interface{}{
        "prompt": ragPrompt,
        "n_predict": 2048,
        "temperature": 0.1,
        "top_p": 0.9,
        "stop": []string{"</s>", "User:", "Question:"},
    }
    
    resp, err := q.client.PostJSON(ctx, q.llamaURL+"/completion", payload)
    return &LLMResponse{Content: resp.Content}, nil
}

func (q *QwenClient) buildRAGPrompt(question string, context []Document) string {
    var contextStr strings.Builder
    
    if len(context) > 0 {
        contextStr.WriteString("Context:\n")
        for i, doc := range context {
            contextStr.WriteString(fmt.Sprintf("[%d] %s\n", i+1, doc.Content))
        }
        contextStr.WriteString("\n")
    }
    
    return fmt.Sprintf(`You are Qwen, an AI assistant for GitOps infrastructure management.

%sQuestion: %s

Instructions:
- Use the provided context to answer accurately
- If context doesn't contain the answer, say so clearly
- Provide specific, actionable guidance
- Reference sources when possible

Answer:`, contextStr.String(), question)
}
```

**2. Data Source Connectors**
```go
// pkg/rag/connectors.go
type DataSource interface {
    Search(ctx context.Context, query string) ([]Document, error)
    IsRelevant(query string) bool
}

// SQLite Memory Connector
type SQLiteMemorySource struct {
    db *sql.DB
}

func (s *SQLiteMemorySource) Search(ctx context.Context, query string) ([]Document, error) {
    rows, err := s.db.QueryContext(ctx, 
        "SELECT content, timestamp FROM conversations WHERE content LIKE ? ORDER BY timestamp DESC LIMIT 10", 
        "%"+query+"%")
    // Convert to documents...
}

// Kubernetes API Connector
type KubernetesSource struct {
    client kubernetes.Interface
}

func (k *KubernetesSource) Search(ctx context.Context, query string) ([]Document, error) {
    pods, err := k.client.CoreV1().Pods("").List(ctx, metav1.ListOptions{})
    // Filter and convert to documents...
}
```

**3. RAG Service Implementation**
```go
// pkg/rag/service.go
type RAGService struct {
    vectorStore     *pgvector.VectorStore
    dataSources     map[string]DataSource
    qwenClient      *QwenClient
    queryAnalyzer   *QueryAnalyzer
    contextBuilder  *ContextBuilder
}

func (r *RAGService) Query(ctx context.Context, question string) (*RAGResponse, error) {
    // 1. Analyze query to determine needed sources
    sources := r.queryAnalyzer.Analyze(question)
    
    // 2. Retrieve context from multiple sources
    context, err := r.contextBuilder.Build(ctx, sources, question)
    if err != nil {
        return nil, err
    }
    
    // 3. Generate response with Qwen
    response, err := r.qwenClient.Generate(ctx, question, context)
    if err != nil {
        return nil, err
    }
    
    return &RAGResponse{
        Answer:  response.Content,
        Sources: r.formatSources(context),
        Model:   "qwen-llamacpp",
    }, nil
}
```

**4. API Endpoint**
```go
// internal/api/rag.go
func (h *Handler) HandleRAGQuery(w http.ResponseWriter, r *http.Request) {
    var query struct {
        Question string   `json:"question"`
        Sources  []string `json:"sources,omitempty"`
    }
    
    json.NewDecoder(r.Body).Decode(&query)
    
    result, err := h.ragService.Query(r.Context(), query.Question)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    json.NewEncoder(w).Encode(result)
}
```

### Phase 3: Documentation Indexing (1 hour)

```go
// cmd/index-docs/main.go
func main() {
    db := connectToPostgreSQL()
    qwenClient := NewQwenClient(os.Getenv("QWEN_LLAMACPP_URL"))
    
    // Index documentation files
    docs := []struct{
        content string
        source  string
        path    string
    }{
        {readFile("core/ai/AGENTS.md"), "agents_docs", "core/ai/AGENTS.md"},
        {readFile("README.md"), "readme", "README.md"},
        {readDirectory("docs/"), "documentation", "docs/"},
        {readDirectory("core/ai/skills/"), "skills", "core/ai/skills/"},
    }
    
    for _, doc := range docs {
        embedding := qwenClient.CreateEmbedding(doc.content)
        
        _, err := db.Exec(`INSERT INTO rag_documents (content, embedding, source_type, source_id) 
                          VALUES ($1, $2, $3, $4)`, 
                          doc.content, embedding, doc.source, doc.path)
        if err != nil {
            log.Printf("Failed to index %s: %v", doc.path, err)
        }
    }
    
    log.Println("Documentation indexing completed")
}
```

### Phase 4: Frontend Integration (1 hour)

```typescript
// src/components/QwenRAGChat.tsx
interface RAGMessage {
  question: string;
  answer: string;
  sources?: Array<{
    type: string;
    content: string;
    confidence: number;
  }>;
  model: string;
  timestamp: Date;
}

const QwenRAGChat: React.FC = () => {
  const [messages, setMessages] = useState<RAGMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);

  const sources = [
    { id: 'documentation', label: 'Documentation', icon: '📚' },
    { id: 'agent_memory', label: 'Agent Memory', icon: '🧠' },
    { id: 'kubernetes', label: 'Kubernetes State', icon: '☸️' },
    { id: 'temporal', label: 'Workflow History', icon: '⏰' },
    { id: 'dashboard', label: 'Dashboard Metrics', icon: '📊' },
  ];

  const sendMessage = async (question: string) => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/v1/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question,
          sources: selectedSources.length > 0 ? selectedSources : undefined
        }),
      });
      
      const result = await response.json();
      
      setMessages(prev => [...prev, {
        question,
        answer: result.answer,
        sources: result.sources,
        model: result.model,
        timestamp: new Date(),
      }]);
    } catch (error) {
      console.error('RAG query failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="qwen-rag-chat">
      <div className="chat-header">
        <h3>🤖 Qwen RAG Assistant</h3>
        <div className="source-selector">
          {sources.map(source => (
            <label key={source.id} className="source-checkbox">
              <input
                type="checkbox"
                checked={selectedSources.includes(source.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedSources(prev => [...prev, source.id]);
                  } else {
                    setSelectedSources(prev => prev.filter(s => s !== source.id));
                  }
                }}
              />
              <span>{source.icon}</span>
              {source.label}
            </label>
          ))}
        </div>
      </div>
      
      <div className="message-list">
        {messages.map((msg, idx) => (
          <div key={idx} className="message-group">
            <div className="user-message">
              <strong>Question:</strong> {msg.question}
            </div>
            <div className="assistant-message">
              <strong>Answer:</strong> {msg.answer}
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources">
                  <strong>Sources:</strong>
                  {msg.sources.map((src, i) => (
                    <div key={i} className="source-item">
                      {src.type}: {src.content.substring(0, 100)}...
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="message-input">
        <input
          type="text"
          placeholder="Ask about your GitOps infrastructure..."
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !isLoading) {
              sendMessage(e.currentTarget.value);
              e.currentTarget.value = '';
            }
          }}
          disabled={isLoading}
            const input = document.querySelector('.message-input input') as HTMLInputElement;
            if (input.value && !isLoading) {
              sendMessage(input.value);
              input.value = '';
            }
          }}
          disabled={isLoading}
        >
          Send
        </button>
      </div>
      
      {isLoading && (
        <div className="loading-indicator">
          <span>🤔 Qwen is thinking...</span>
        </div>
      )}
    </div>
  );
};

export default QwenRAGChat;
```

### Phase 5: Deployment & Testing (30 minutes)

**1. Update Dashboard Deployment**
```bash
# Apply database changes
kubectl exec -it postgres-pod -- psql -U dashboard_user -d ai_agents_dashboard -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Deploy updated dashboard
kubectl apply -f core/ai/runtime/dashboard/deployment/kubernetes/

# Run documentation indexing
kubectl run rag-indexer --image=your-dashboard-image --restart=Never -- \
  /index-docs --qwen-url=http://llamacpp-service:8080
```

**2. Integration Tests**
```bash
# Test RAG endpoint
curl -X POST http://localhost:8081/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What skills are available for cost optimization?"}'

# Test frontend
# Navigate to dashboard and verify Qwen RAG chat appears
```

## Benefits

### Immediate Benefits
- **Zero additional infrastructure**: Uses existing Qwen + llama.cpp
- **Leverages current data**: Utilizes all existing data sources
- **Self-hosted privacy**: No external API calls
- **Consistent model experience**: Same Qwen model across all features

### Long-term Benefits
- **Intelligent assistance**: Context-aware answers about infrastructure
- **Knowledge retention**: Learns from operations and conversations
- **Multi-source insights**: Combines documentation, history, and current state
- **Scalable architecture**: Easy to add new data sources

## Success Metrics

### Technical Metrics
- RAG query response time < 5 seconds
- 95%+ successful query completion rate
- Document indexing covers 100% of relevant documentation

### User Experience Metrics
- Users can find answers without manual documentation search
- Reduction in support tickets for common questions
- Improved operator efficiency in troubleshooting

### System Metrics
- No performance degradation in existing dashboard features
- Minimal resource overhead for RAG functionality
- Stable operation under concurrent load

## Rollback Plan

If issues arise:
1. **Disable RAG**: Set `RAG_ENABLED=false` in environment variables
2. **Remove pgvector**: Drop extension and tables from PostgreSQL
3. **Frontend fallback**: Hide RAG chat component
4. **Restore backup**: Use database backup before RAG changes

## Next Steps

1. **Confirm existing Qwen + llama.cpp setup details**
2. **Deploy Phase 1**: Database setup
3. **Implement Phase 2**: Backend RAG service
4. **Complete Phase 3-5**: Full integration
5. **Monitor and optimize** based on usage patterns

---

**Status**: Ready for implementation pending confirmation of existing infrastructure details.
