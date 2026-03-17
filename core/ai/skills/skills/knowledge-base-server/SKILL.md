---
name: knowledge-base-server
description: >
  Contextual reasoning and knowledge retrieval system that indexes documents, provides
  semantic search capabilities, analyzes meeting transcripts, tracks decision history,
  and builds knowledge graphs for intelligent information retrieval and contextual insights.
metadata:
  risk_level: low
  autonomy: high
  layer: temporal
  human_gate: Content approval required for public knowledge base updates
---

# Knowledge Base Server Skill

## Overview

The Knowledge Base Server skill provides comprehensive contextual reasoning and knowledge retrieval capabilities. It indexes documents, performs semantic search, analyzes meeting transcripts, tracks decision history, and builds knowledge graphs to provide intelligent information retrieval and contextual insights.

## Capabilities

### Core Functions

- **Document Indexing**: Indexes and processes various document types for retrieval
- **Semantic Search**: Performs intelligent search using embeddings and similarity matching
- **Meeting Transcript Analysis**: Extracts decisions, action items, and insights from transcripts
- **Decision History Tracking**: Maintains searchable database of organizational decisions
- **Knowledge Graph Construction**: Builds and queries relationship graphs between entities
- **Contextual Information Retrieval**: Provides context-aware information for topics

### Supported Document Types

- **Runbooks**: Technical procedures and troubleshooting guides
- **Meeting Transcripts**: Meeting records and discussions
- **Decision Records**: Formal decision documentation
- **Policies**: Organizational policies and procedures
- **Technical Documentation**: Architecture docs, API docs, and technical specifications

### Search Capabilities

1. **Semantic Search**: Vector-based similarity matching
2. **Keyword Search**: Traditional text-based search
3. **Hybrid Search**: Combined semantic and keyword approaches
4. **Contextual Search**: Search with additional context and filters
5. **Relationship-based Search**: Search using knowledge graph relationships

## Usage

### Document Indexing

```bash
# Index a single document
skill invoke knowledge-base index-document --document-path docs/runbook.md --document-type runbook

# Index entire directory
skill invoke knowledge-base index-directory --directory-path ./docs --recursive

# Batch index with metadata
skill invoke knowledge-base index-batch --config indexing-config.yaml

# Reindex existing documents
skill invoke knowledge-base reindex --document-type runbook --force
```

### Knowledge Search

```bash
# Semantic search
skill invoke knowledge-base search --query "database troubleshooting" --search-type semantic --limit 10

# Keyword search
skill invoke knowledge-base search --query "AWS S3" --search-type keyword --document-types runbook,policy

# Hybrid search with filters
skill invoke knowledge-base search --query "incident response" --search-type hybrid \
  --document-types runbook,meeting_transcript --similarity-threshold 0.7

# Contextual search
skill invoke knowledge-base contextual-search --topic "cloud migration" --context-type historical_decisions
```

### Meeting Analysis

```bash
# Analyze meeting transcript
skill invoke knowledge-base analyze-meeting --transcript-path meetings/2024-03-15-team-meeting.txt

# Extract decisions only
skill invoke knowledge-base extract-decisions --transcript-path meetings/strategy-session.txt

# Generate meeting summary
skill invoke knowledge-base summarize-meeting --transcript-path meetings/retrospective.txt --include-action-items

# Batch analyze meetings
skill invoke knowledge-base batch-analyze-meetings --directory-path meetings/ --date-range 2024-01-01:2024-03-31
```

### Decision Tracking

```bash
# Track new decision
skill invoke knowledge-base track-decision --decision-id DEC-001 \
  --title "Adopt Kubernetes for new services" \
  --description "Decision to migrate all new microservices to Kubernetes" \
  --decision-maker "CTO" --date "2024-03-15" \
  --context "Cost optimization and scalability requirements"

# Update decision with related decisions
skill invoke knowledge-base relate-decisions --decision-id DEC-001 \
  --related-decisions DEC-002,DEC-003

# Search decision history
skill invoke knowledge-base search-decisions --query "cloud infrastructure" --date-range 2024-01-01:2024-12-31

# Generate decision timeline
skill invoke knowledge-base decision-timeline --project "web-platform" --format HTML
```

### Knowledge Graph Operations

```bash
# Add entity to knowledge graph
skill invoke knowledge-base add-entity --entity-id "kubernetes" --entity-type technology \
  --name "Kubernetes" --properties '{"category": "orchestration", "vendor": "CNCF"}'

# Add relationship
skill invoke knowledge-base add-relationship --from-entity "kubernetes" --to-entity "docker" \
  --relationship-type "builds_on" --properties '{"strength": "strong"}'

# Query knowledge graph
skill invoke knowledge-base query-graph --query '{"entity": "kubernetes", "depth": 2}'

# Get context for entity
skill invoke knowledge-base get-context --entity "kubernetes" --context-type related_documents
```

### Contextual Information

```bash
# Get historical context
skill invoke knowledge-base get-context --topic "microservices" --context-type historical_decisions \
  --time-range 6m --include-related

# Get expertise areas
skill invoke knowledge-base get-expertise --topic "database optimization" --include-experts

# Get recent changes
skill invoke knowledge-base recent-changes --topic "security policies" --time-range 30d

# General context retrieval
skill invoke knowledge-base context --topic "cloud migration" --depth 3 --breadth 5
```

## Configuration

### Required Environment Variables

```bash
# Vector Database (for production use)
VECTOR_DB_URL=your_vector_database_url
VECTOR_DB_API_KEY=your_vector_db_api_key

# Document Processing
DOCUMENT_PROCESSING_TIMEOUT=300
MAX_DOCUMENT_SIZE=50MB
EMBEDDING_MODEL=text-embedding-ada-002

# Search Configuration
DEFAULT_SEARCH_LIMIT=10
SIMILARITY_THRESHOLD=0.7
MAX_SEARCH_RESULTS=100

# Storage Configuration
KNOWLEDGE_BASE_PATH=/data/knowledge-base
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
RETENTION_DAYS=365
```

### Skill Configuration

```yaml
# .claude/skills/knowledge-base-server/config.yaml
document_processing:
  supported_formats:
    - markdown
    - text
    - pdf
    - docx
    - html
    - json
    - yaml
  
  chunking:
    strategy: semantic
    max_chunk_size: 1000
    overlap: 200
    min_chunk_size: 100
  
  embeddings:
    model: text-embedding-ada-002
    dimension: 1536
    batch_size: 100
    cache_embeddings: true
  
  entity_extraction:
    enabled: true
    entities:
      - person
      - organization
      - technology
      - project
      - decision
      - policy
    confidence_threshold: 0.7

search_configuration:
  semantic_search:
    enabled: true
    similarity_threshold: 0.7
    max_results: 50
    rerank_results: true
  
  keyword_search:
    enabled: true
    boost_recent: true
    boost_important: true
    fuzzy_matching: true
  
  hybrid_search:
    semantic_weight: 0.6
    keyword_weight: 0.4
    fusion_algorithm: reciprocal_rank_fusion
  
  filters:
    document_types:
      - runbook
      - meeting_transcript
      - decision_record
      - policy
      - technical_doc
    date_ranges:
      recent: 7d
      month: 30d
      quarter: 90d
      year: 365d

knowledge_graph:
  node_types:
    - technology
    - person
    - organization
    - project
    - decision
    - concept
    - location
  
  relationship_types:
    - uses
    - implements
    - decides_on
    - owns
    - depends_on
    - relates_to
    - manages
    - documents
  
  graph_algorithms:
    - page_rank
    - community_detection
    - shortest_path
    - centrality_measures
  
  visualization:
    enabled: true
    layout: force_directed
    node_size_by: importance
    edge_width_by: strength

meeting_analysis:
  transcript_processing:
    speaker_diarization: true
    sentiment_analysis: true
    topic_modeling: true
    action_item_extraction: true
  
  decision_extraction:
    patterns:
      - "decided to"
      - "agreed that"
      - "concluded"
      - "resolved"
    confidence_threshold: 0.8
    require_context: true
  
  action_item_extraction:
    patterns:
      - "will"
      - "should"
      - "need to"
      - "action item"
    assignee_extraction: true
    due_date_extraction: true
  
  summarization:
    executive_summary: true
    key_decisions: true
    action_items: true
    participant_contributions: true

decision_tracking:
  required_fields:
    - title
    - description
    - decision_maker
    - date
  
  optional_fields:
    - context
    - alternatives_considered
    - rationale
    - impact
    - stakeholders
    - implementation_status
  
  relationship_types:
    - supersedes
    - implements
    - relates_to
    - conflicts_with
  
  lifecycle_stages:
    - proposed
    - decided
    - implemented
    - evaluated
    - archived

indexing_configuration:
  auto_indexing:
    enabled: true
    watch_directories:
      - ./docs
      - ./meetings
      - ./decisions
    file_patterns:
      - "*.md"
      - "*.txt"
      - "*.pdf"
      - "*.docx"
    ignore_patterns:
      - "*.tmp"
      - "*.bak"
      - ".*"
  
  scheduling:
    full_reindex: "0 3 * * 0"  # Weekly on Sunday at 3 AM
    incremental_update: "0 * * * *"  # Every hour
    cleanup: "0 4 * * *"  # Daily at 4 AM
  
  performance:
    batch_size: 50
    parallel_workers: 4
    memory_limit: 2GB
    timeout: 300

api_configuration:
  endpoints:
    search: /api/v1/search
    documents: /api/v1/documents
    decisions: /api/v1/decisions
    graph: /api/v1/graph
    context: /api/v1/context
  
  authentication:
    enabled: true
    method: api_key
    rate_limiting: true
    requests_per_minute: 100
  
  caching:
    enabled: true
    ttl: 3600  # 1 hour
    max_size: 1GB
    strategy: lru
```

## MCP Server Integration

This skill integrates with the `knowledge-base` MCP server for enhanced capabilities:

### Available MCP Tools

- `index_document`: Index documents for knowledge retrieval
- `search_knowledge`: Search knowledge base using semantic or keyword search
- `analyze_meeting_transcript`: Analyze meeting transcripts for decisions and action items
- `track_decision_history`: Track and retrieve decision history and context
- `build_knowledge_graph`: Build and query knowledge graph relationships
- `get_contextual_information`: Get contextual information for topics

### MCP Usage Example

```javascript
// Using the MCP server directly
const searchResults = await mcp.call('search_knowledge', {
  query: 'database performance optimization',
  search_type: 'semantic',
  document_types: ['runbook', 'technical_doc'],
  limit: 10,
  similarity_threshold: 0.7
});

const meetingAnalysis = await mcp.call('analyze_meeting_transcript', {
  transcript_path: 'meetings/2024-03-15-db-team.txt',
  extract_decisions: true,
  extract_action_items: true,
  generate_summary: true
});

const decisionContext = await mcp.call('get_contextual_information', {
  topic: 'cloud migration strategy',
  context_type: 'historical_decisions',
  time_range: '6m',
  include_related: true
});
```

## Implementation Details

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Document Sources│    │ Processing Engine │    │ Search Engine   │
│                 │    │                  │    │                 │
│ • File System   │───▶│ • Text Processing│───▶│ • Vector Search │
│ • APIs          │    │ • Entity Extract │    │ • Keyword Search │
│ • Databases     │    │ • Embedding Gen  │    │ • Hybrid Search  │
│ • Web Crawlers  │    │ • Chunking       │    │ • Ranking        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Knowledge Graph │    │ Meeting Analysis │    │ Context Engine  │
│                 │    │                  │    │                 │
│ • Entity Mapping│    │ • Transcript Proc│    │ • Context Retrieval│
│ • Relationship  │    │ • Decision Extract│    │ • Reasoning     │
│ • Graph Queries │    │ • Action Items   │    │ • Insight Gen   │
│ • Visualization │    │ • Summarization   │    │ • Recommendations│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Document Processing Pipeline

1. **Ingestion**: Read and parse documents from various sources
2. **Preprocessing**: Clean text, remove noise, normalize formatting
3. **Chunking**: Split documents into semantic chunks
4. **Entity Extraction**: Identify and extract entities and relationships
5. **Embedding Generation**: Create vector embeddings for semantic search
6. **Indexing**: Store processed content in searchable indexes
7. **Knowledge Graph Update**: Update knowledge graph with new entities and relationships

### Search Algorithm

#### Semantic Search
```python
def semantic_search(query, documents, threshold=0.7, limit=10):
    """
    Perform semantic search using vector similarity
    """
    query_embedding = generate_embedding(query)
    
    similarities = []
    for doc in documents:
        similarity = cosine_similarity(query_embedding, doc.embedding)
        if similarity >= threshold:
            similarities.append((doc, similarity))
    
    # Sort by similarity and return top results
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:limit]
```

#### Hybrid Search
```python
def hybrid_search(query, documents, semantic_weight=0.6, keyword_weight=0.4):
    """
    Combine semantic and keyword search results
    """
    semantic_results = semantic_search(query, documents)
    keyword_results = keyword_search(query, documents)
    
    # Reciprocal rank fusion
    all_docs = set(doc for doc, _ in semantic_results + keyword_results)
    fused_scores = {}
    
    for doc in all_docs:
        semantic_rank = next((i for i, (d, _) in enumerate(semantic_results) if d == doc), float('inf'))
        keyword_rank = next((i for i, (d, _) in enumerate(keyword_results) if d == doc), float('inf'))
        
        semantic_score = 1 / (semantic_rank + 1) if semantic_rank != float('inf') else 0
        keyword_score = 1 / (keyword_rank + 1) if keyword_rank != float('inf') else 0
        
        fused_scores[doc] = semantic_weight * semantic_score + keyword_weight * keyword_score
    
    return sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
```

### Meeting Analysis Algorithm

#### Decision Extraction
```python
def extract_decisions(transcript):
    """
    Extract decisions from meeting transcript using pattern matching and NLP
    """
    decisions = []
    
    # Pattern-based extraction
    decision_patterns = [
        r'(decided|agreed|concluded|resolved|determined)\s+to\s+(.+)',
        r'it\s+was\s+(decided|agreed)\s+that\s+(.+)',
        r'we\s+(decide|agree)\s+to\s+(.+)'
    ]
    
    for sentence in transcript.sentences:
        for pattern in decision_patterns:
            match = re.search(pattern, sentence.text, re.IGNORECASE)
            if match:
                decision = {
                    'text': sentence.text,
                    'decision': match.group(2),
                    'confidence': calculate_confidence(match, sentence),
                    'context': get_context(sentence, transcript),
                    'timestamp': sentence.timestamp
                }
                decisions.append(decision)
    
    # Filter by confidence threshold
    return [d for d in decisions if d['confidence'] >= 0.7]
```

#### Action Item Extraction
```python
def extract_action_items(transcript):
    """
    Extract action items with assignees and due dates
    """
    action_items = []
    
    action_patterns = [
        r'(\w+)\s+(will|should|needs?\s+to)\s+(.+)',
        r'action\s+item:\s*(.+)',
        r'todo:\s*(.+)'
    ]
    
    for sentence in transcript.sentences:
        for pattern in action_patterns:
            match = re.search(pattern, sentence.text, re.IGNORECASE)
            if match:
                action_item = {
                    'text': sentence.text,
                    'action': match.group(-1),
                    'assignee': extract_assignee(match, sentence),
                    'due_date': extract_due_date(match, sentence),
                    'confidence': calculate_confidence(match, sentence)
                }
                action_items.append(action_item)
    
    return action_items
```

### Knowledge Graph Construction

#### Entity Relationship Extraction
```python
def extract_relationships(text, entities):
    """
    Extract relationships between entities in text
    """
    relationships = []
    
    # Dependency parsing for relationship extraction
    doc = nlp(text)
    
    for token in doc:
        if token.dep_ in ['nsubj', 'dobj', 'pobj']:
            head_entity = find_entity(token.head.text, entities)
            child_entity = find_entity(token.text, entities)
            
            if head_entity and child_entity:
                relationship = {
                    'from_entity': head_entity['id'],
                    'to_entity': child_entity['id'],
                    'relationship_type': map_dependency_to_relationship(token.dep_),
                    'confidence': calculate_relationship_confidence(token),
                    'context': token.sent.text
                }
                relationships.append(relationship)
    
    return relationships
```

## Best Practices

### 1. Document Management
- Use consistent naming conventions for documents
- Include metadata tags for better categorization
- Regularly update and maintain document quality
- Implement version control for important documents

### 2. Knowledge Organization
- Create hierarchical taxonomies for better navigation
- Use consistent entity naming and categorization
- Maintain clean knowledge graph relationships
- Regularly review and update knowledge structures

### 3. Search Optimization
- Use descriptive and comprehensive document titles
- Include relevant keywords and tags
- Structure documents for optimal chunking
- Regularly evaluate and improve search relevance

### 4. Meeting Documentation
- Use consistent transcript formatting
- Clearly mark decisions and action items
- Include participant names and roles
- Provide context and background information

## Troubleshooting

### Common Issues

**Document Indexing Failures**
```bash
# Check document format support
skill invoke knowledge-base check-format --document-path docs/example.pdf

# Validate document structure
skill invoke knowledge-base validate-document --document-path docs/example.md

# Debug indexing process
export KNOWLEDGE_BASE_DEBUG=true
skill invoke knowledge-base index-document --document-path docs/example.md --debug
```

**Search Quality Issues**
```bash
# Analyze search results
skill invoke knowledge-base analyze-search --query "test query" --explain-ranking

# Test similarity thresholds
skill invoke knowledge-base test-thresholds --query "test query" --range 0.5:0.9

# Evaluate embedding quality
skill invoke knowledge-base evaluate-embeddings --sample-documents 100
```

**Knowledge Graph Issues**
```bash
# Check graph consistency
skill invoke knowledge-base validate-graph --check-orphans --check-cycles

# Analyze entity relationships
skill invoke knowledge-base analyze-relationships --entity "kubernetes"

# Debug graph construction
skill invoke knowledge-base debug-graph --document-path docs/architecture.md
```

### Debug Mode

```bash
# Enable comprehensive debugging
export KNOWLEDGE_BASE_DEBUG=true
export KNOWLEDGE_BASE_TRACE=true
skill invoke knowledge-base search --query "test" --debug --trace --verbose
```

## Integration Examples

### CI/CD Pipeline Integration

```yaml
# .github/workflows/knowledge-base-update.yml
name: Update Knowledge Base
on:
  push:
    paths:
      - 'docs/**'
      - 'meetings/**'
      - 'decisions/**'

jobs:
  update-knowledge-base:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Update Knowledge Base
        run: |
          skill invoke knowledge-base index-directory --directory-path ./docs --recursive
          skill invoke knowledge-base index-directory --directory-path ./meetings --recursive
          skill invoke knowledge-base index-directory --directory-path ./decisions --recursive
      - name: Validate Knowledge Base
        run: |
          skill invoke knowledge-base validate --check-consistency --check-orphans
      - name: Generate Knowledge Base Report
        run: |
          skill invoke knowledge-base generate-report --format HTML --output knowledge-base-report.html
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: knowledge-base-report
          path: knowledge-base-report.html
```

### Slack Integration

```javascript
// Slack bot for knowledge search
app.command('/knowledge', async ({ command, ack, say }) => {
  await ack();
  
  const query = command.text;
  
  try {
    const results = await skill.invoke('knowledge-base', {
      action: 'search',
      query: query,
      search_type: 'hybrid',
      limit: 5
    });
    
    const blocks = results.map((result, index) => ({
      type: 'section',
      text: {
        type: 'mrkdwn',
        text: `*${index + 1}. ${result.title}*\n${result.excerpt}\n_Relevance: ${result.similarity.toFixed(2)}_`
      }
    }));
    
    await say({
      text: `📚 Knowledge Search Results for "${query}"`,
      blocks
    });
  } catch (error) {
    await say(`❌ Error searching knowledge base: ${error.message}`);
  }
});
```

### API Integration

```javascript
// REST API for knowledge base operations
app.get('/api/knowledge/search', async (req, res) => {
  const { query, type = 'hybrid', limit = 10 } = req.query;
  
  try {
    const results = await skill.invoke('knowledge-base', {
      action: 'search',
      query: query,
      search_type: type,
      limit: parseInt(limit)
    });
    
    res.json({
      query,
      type,
      total_results: results.length,
      results
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/knowledge/documents', async (req, res) => {
  const { document_path, document_type, metadata } = req.body;
  
  try {
    const result = await skill.invoke('knowledge-base', {
      action: 'index-document',
      document_path: document_path,
      document_type: document_type,
      metadata: metadata
    });
    
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

## Performance Considerations

### Optimization Tips

1. **Embedding Caching**: Cache frequently used embeddings to reduce computation
2. **Batch Processing**: Process documents in batches for better efficiency
3. **Incremental Updates**: Only update changed content instead of full reindexing
4. **Parallel Processing**: Use multiple workers for document processing

### Resource Usage

- **Memory**: ~4GB for large knowledge bases with embeddings
- **CPU**: High usage during embedding generation and processing
- **Storage**: ~10GB for knowledge base with 1000+ documents
- **Network**: Moderate usage during API calls and data transfers

## Security Considerations

### Data Protection

- All documents are encrypted at rest
- Search queries and results are logged for audit
- Access control based on user roles and permissions
- Sensitive information is redacted in search results

### Access Control

- Role-based access for different document types
- API authentication and rate limiting
- Secure embedding model API key management
- Audit logging for all knowledge base operations

## Version History

### v1.0.0
- Initial release with basic document indexing and search
- Support for markdown and text documents
- Simple keyword search functionality

### v1.1.0
- Added semantic search with embeddings
- Meeting transcript analysis capabilities
- Basic knowledge graph construction

### v1.2.0
- Enhanced search with hybrid approach
- Decision tracking and history
- Contextual information retrieval

### v1.3.0
- Advanced knowledge graph algorithms
- Real-time document processing
- Comprehensive API and integration capabilities

## Support and Contributing

### Getting Help

- Documentation: `/docs/knowledge-base-server.md`
- Examples: `/examples/knowledge-base/`
- Community: `#knowledge-base` Slack channel

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

### License

This skill is licensed under the MIT License. See LICENSE file for details.
