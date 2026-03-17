#!/usr/bin/env node

/**
 * Knowledge Base Server MCP Server
 * 
 * This MCP server provides contextual reasoning and knowledge retrieval:
 * - Document indexing and search
 * - Contextual information retrieval
 * - Meeting transcript analysis
 * - Decision history tracking
 * - Knowledge graph construction
 * - Semantic search capabilities
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} = require('@modelcontextprotocol/sdk/types.js');

// Vector database and text processing
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

class KnowledgeBaseServer {
  constructor() {
    this.server = new Server(
      {
        name: 'knowledge-base-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.setupErrorHandling();
    
    // In-memory knowledge store (in production, use a proper vector DB)
    this.knowledgeStore = new Map();
    this.documentIndex = new Map();
  }

  setupErrorHandling() {
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'index_document',
          description: 'Index a document for knowledge retrieval',
          inputSchema: {
            type: 'object',
            properties: {
              document_path: {
                type: 'string',
                description: 'Path to the document to index'
              },
              document_type: {
                type: 'string',
                enum: ['runbook', 'meeting_transcript', 'decision_record', 'policy', 'technical_doc'],
                description: 'Type of document'
              },
              metadata: {
                type: 'object',
                description: 'Additional metadata for the document',
                properties: {
                  author: { type: 'string' },
                  date: { type: 'string' },
                  tags: { type: 'array', items: { type: 'string' } },
                  category: { type: 'string' }
                }
              },
              force_reindex: {
                type: 'boolean',
                default: false,
                description: 'Force reindexing even if already indexed'
              }
            }
          }
        },
        {
          name: 'search_knowledge',
          description: 'Search knowledge base using semantic or keyword search',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Search query'
              },
              search_type: {
                type: 'string',
                enum: ['semantic', 'keyword', 'hybrid'],
                default: 'hybrid',
                description: 'Type of search to perform'
              },
              document_types: {
                type: 'array',
                items: { type: 'string' },
                description: 'Filter by document types'
              },
              limit: {
                type: 'number',
                default: 10,
                description: 'Maximum number of results to return'
              },
              similarity_threshold: {
                type: 'number',
                default: 0.7,
                description: 'Minimum similarity threshold for semantic search'
              }
            }
          }
        },
        {
          name: 'analyze_meeting_transcript',
          description: 'Analyze meeting transcript for decisions and action items',
          inputSchema: {
            type: 'object',
            properties: {
              transcript_path: {
                type: 'string',
                description: 'Path to meeting transcript file'
              },
              extract_decisions: {
                type: 'boolean',
                default: true,
                description: 'Extract decisions from transcript'
              },
              extract_action_items: {
                type: 'boolean',
                default: true,
                description: 'Extract action items from transcript'
              },
              extract_participants: {
                type: 'boolean',
                default: true,
                description: 'Extract participants and their contributions'
              },
              generate_summary: {
                type: 'boolean',
                default: true,
                description: 'Generate meeting summary'
              }
            }
          }
        },
        {
          name: 'track_decision_history',
          description: 'Track and retrieve decision history and context',
          inputSchema: {
            type: 'object',
            properties: {
              decision_id: {
                type: 'string',
                description: 'Unique decision identifier'
              },
              decision_data: {
                type: 'object',
                description: 'Decision data to track',
                properties: {
                  title: { type: 'string' },
                  description: { type: 'string' },
                  decision_maker: { type: 'string' },
                  date: { type: 'string' },
                  context: { type: 'string' },
                  alternatives_considered: { type: 'array', items: { type: 'string' } },
                  rationale: { type: 'string' },
                  impact: { type: 'string' }
                }
              },
              related_decisions: {
                type: 'array',
                items: { type: 'string' },
                description: 'IDs of related decisions'
              }
            }
          }
        },
        {
          name: 'build_knowledge_graph',
          description: 'Build and query knowledge graph relationships',
          inputSchema: {
            type: 'object',
            properties: {
              operation: {
                type: 'string',
                enum: ['add_entity', 'add_relationship', 'query_graph', 'get_context'],
                description: 'Operation to perform on knowledge graph'
              },
              entity_data: {
                type: 'object',
                description: 'Entity data for add_entity operation',
                properties: {
                  id: { type: 'string' },
                  type: { type: 'string' },
                  name: { type: 'string' },
                  properties: { type: 'object' }
                }
              },
              relationship_data: {
                type: 'object',
                description: 'Relationship data for add_relationship operation',
                properties: {
                  from_entity: { type: 'string' },
                  to_entity: { type: 'string' },
                  relationship_type: { type: 'string' },
                  properties: { type: 'object' }
                }
              },
              query: {
                type: 'object',
                description: 'Query parameters for query_graph operation'
              }
            }
          }
        },
        {
          name: 'get_contextual_information',
          description: 'Get contextual information for a given topic or entity',
          inputSchema: {
            type: 'object',
            properties: {
              topic: {
                type: 'string',
                description: 'Topic to get contextual information for'
              },
              context_type: {
                type: 'string',
                enum: ['historical_decisions', 'related_documents', 'expertise_areas', 'recent_changes'],
                description: 'Type of context to retrieve'
              },
              time_range: {
                type: 'string',
                description: 'Time range for context (e.g., "30d", "3m", "1y")'
              },
              include_related: {
                type: 'boolean',
                default: true,
                description: 'Include related topics and entities'
              }
            }
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'index_document':
            return await this.indexDocument(args);
          case 'search_knowledge':
            return await this.searchKnowledge(args);
          case 'analyze_meeting_transcript':
            return await this.analyzeMeetingTranscript(args);
          case 'track_decision_history':
            return await this.trackDecisionHistory(args);
          case 'build_knowledge_graph':
            return await this.buildKnowledgeGraph(args);
          case 'get_contextual_information':
            return await this.getContextualInformation(args);
          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
        }
      } catch (error) {
        console.error(`Error in ${name}:`, error);
        throw new McpError(ErrorCode.InternalError, `Tool execution failed: ${error.message}`);
      }
    });
  }

  async indexDocument(args) {
    const { document_path, document_type, metadata = {}, force_reindex = false } = args;
    
    try {
      // Generate document ID
      const document_id = this.generateDocumentId(document_path);
      
      // Check if already indexed
      if (!force_reindex && this.documentIndex.has(document_id)) {
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                type: 'document_already_indexed',
                document_id,
                document_path,
                message: 'Document already indexed. Use force_reindex=true to reindex.'
              }, null, 2)
            }
          ]
        };
      }
      
      // Read and process document
      const document_content = await this.readDocument(document_path);
      const processed_content = await this.processDocumentContent(document_content);
      
      // Create document entry
      const document_entry = {
        id: document_id,
        path: document_path,
        type: document_type,
        metadata: {
          ...metadata,
          indexed_at: new Date().toISOString(),
          content_length: document_content.length,
          word_count: processed_content.words.length
        },
        content: processed_content,
        embeddings: await this.generateEmbeddings(processed_content.text)
      };
      
      // Store in knowledge base
      this.knowledgeStore.set(document_id, document_entry);
      this.documentIndex.set(document_id, {
        id: document_id,
        type: document_type,
        path: document_path,
        metadata: document_entry.metadata
      });
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'document_indexed',
              document_id,
              document_path,
              document_type,
              metadata: document_entry.metadata,
              processing_stats: {
                words_processed: processed_content.words.length,
                sentences_processed: processed_content.sentences.length,
                entities_extracted: processed_content.entities.length
              }
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Document indexing failed: ${error.message}`);
    }
  }

  async searchKnowledge(args) {
    const { query, search_type = 'hybrid', document_types, limit = 10, similarity_threshold = 0.7 } = args;
    
    try {
      const search_results = {
        query,
        search_type,
        timestamp: new Date().toISOString(),
        results: [],
        total_found: 0
      };
      
      // Get documents to search
      let documentsToSearch = Array.from(this.knowledgeStore.values());
      
      // Filter by document types if specified
      if (document_types && document_types.length > 0) {
        documentsToSearch = documentsToSearch.filter(doc => 
          document_types.includes(doc.type)
        );
      }
      
      // Perform search based on type
      if (search_type === 'semantic') {
        const query_embedding = await this.generateEmbeddings(query);
        search_results.results = await this.performSemanticSearch(
          query_embedding, 
          documentsToSearch, 
          similarity_threshold, 
          limit
        );
      } else if (search_type === 'keyword') {
        search_results.results = await this.performKeywordSearch(
          query, 
          documentsToSearch, 
          limit
        );
      } else if (search_type === 'hybrid') {
        search_results.results = await this.performHybridSearch(
          query, 
          documentsToSearch, 
          similarity_threshold, 
          limit
        );
      }
      
      search_results.total_found = search_results.results.length;
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'knowledge_search_results',
              ...search_results
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Knowledge search failed: ${error.message}`);
    }
  }

  async analyzeMeetingTranscript(args) {
    const { transcript_path, extract_decisions = true, extract_action_items = true, extract_participants = true, generate_summary = true } = args;
    
    try {
      // Read transcript
      const transcript_content = await this.readDocument(transcript_path);
      
      const analysis_result = {
        transcript_path,
        timestamp: new Date().toISOString(),
        analysis: {}
      };
      
      // Extract participants
      if (extract_participants) {
        analysis_result.analysis.participants = await this.extractParticipants(transcript_content);
      }
      
      // Extract decisions
      if (extract_decisions) {
        analysis_result.analysis.decisions = await this.extractDecisions(transcript_content);
      }
      
      // Extract action items
      if (extract_action_items) {
        analysis_result.analysis.action_items = await this.extractActionItems(transcript_content);
      }
      
      // Generate summary
      if (generate_summary) {
        analysis_result.analysis.summary = await this.generateMeetingSummary(transcript_content, analysis_result.analysis);
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'meeting_transcript_analysis',
              ...analysis_result
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Meeting transcript analysis failed: ${error.message}`);
    }
  }

  async trackDecisionHistory(args) {
    const { decision_id, decision_data, related_decisions = [] } = args;
    
    try {
      const decision_record = {
        id: decision_id,
        ...decision_data,
        related_decisions,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      // Store decision record
      this.knowledgeStore.set(`decision:${decision_id}`, decision_record);
      
      // Update knowledge graph relationships
      if (related_decisions.length > 0) {
        for (const related_id of related_decisions) {
          await this.addDecisionRelationship(decision_id, related_id);
        }
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'decision_tracked',
              decision_record,
              message: 'Decision successfully tracked and indexed'
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Decision tracking failed: ${error.message}`);
    }
  }

  async buildKnowledgeGraph(args) {
    const { operation, entity_data, relationship_data, query } = args;
    
    try {
      let result;
      
      switch (operation) {
        case 'add_entity':
          result = await this.addKnowledgeEntity(entity_data);
          break;
        case 'add_relationship':
          result = await this.addKnowledgeRelationship(relationship_data);
          break;
        case 'query_graph':
          result = await this.queryKnowledgeGraph(query);
          break;
        case 'get_context':
          result = await this.getGraphContext(query);
          break;
        default:
          throw new Error(`Unknown operation: ${operation}`);
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'knowledge_graph_operation',
              operation,
              result,
              timestamp: new Date().toISOString()
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Knowledge graph operation failed: ${error.message}`);
    }
  }

  async getContextualInformation(args) {
    const { topic, context_type, time_range, include_related = true } = args;
    
    try {
      const context_result = {
        topic,
        context_type,
        time_range,
        timestamp: new Date().toISOString(),
        information: {}
      };
      
      // Get contextual information based on type
      switch (context_type) {
        case 'historical_decisions':
          context_result.information = await this.getHistoricalDecisions(topic, time_range);
          break;
        case 'related_documents':
          context_result.information = await this.getRelatedDocuments(topic, time_range);
          break;
        case 'expertise_areas':
          context_result.information = await this.getExpertiseAreas(topic);
          break;
        case 'recent_changes':
          context_result.information = await this.getRecentChanges(topic, time_range);
          break;
        default:
          context_result.information = await this.getGeneralContext(topic);
      }
      
      // Include related information if requested
      if (include_related) {
        context_result.related_topics = await this.getRelatedTopics(topic);
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              type: 'contextual_information',
              ...context_result
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      throw new Error(`Contextual information retrieval failed: ${error.message}`);
    }
  }

  // Helper methods
  generateDocumentId(documentPath) {
    return crypto.createHash('sha256').update(documentPath).digest('hex').substring(0, 16);
  }

  async readDocument(documentPath) {
    try {
      return await fs.readFile(documentPath, 'utf8');
    } catch (error) {
      throw new Error(`Failed to read document: ${error.message}`);
    }
  }

  async processDocumentContent(content) {
    // Simple text processing (in production, use NLP libraries)
    const words = content.toLowerCase().match(/\b\w+\b/g) || [];
    const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const entities = this.extractEntities(content);
    
    return {
      text: content,
      words,
      sentences,
      entities,
      processed_at: new Date().toISOString()
    };
  }

  extractEntities(text) {
    // Simple entity extraction (in production, use NER)
    const entities = [];
    
    // Extract emails
    const emailMatches = text.match(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g);
    if (emailMatches) {
      entities.push(...emailMatches.map(email => ({ type: 'email', value: email })));
    }
    
    // Extract URLs
    const urlMatches = text.match(/https?:\/\/[^\s]+/g);
    if (urlMatches) {
      entities.push(...urlMatches.map(url => ({ type: 'url', value: url })));
    }
    
    // Extract dates
    const dateMatches = text.match(/\b\d{4}-\d{2}-\d{2}\b/g);
    if (dateMatches) {
      entities.push(...dateMatches.map(date => ({ type: 'date', value: date })));
    }
    
    return entities;
  }

  async generateEmbeddings(text) {
    // Mock embedding generation (in production, use actual embedding model)
    const words = text.toLowerCase().split(/\s+/);
    const embedding = new Array(384).fill(0);
    
    // Simple word-based embedding (for demonstration)
    words.forEach((word, index) => {
      const hash = this.simpleHash(word);
      embedding[index % embedding.length] = (hash % 100) / 100;
    });
    
    return embedding;
  }

  simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  async performSemanticSearch(queryEmbedding, documents, threshold, limit) {
    const results = [];
    
    for (const doc of documents) {
      if (!doc.embeddings) continue;
      
      const similarity = this.calculateCosineSimilarity(queryEmbedding, doc.embeddings);
      
      if (similarity >= threshold) {
        results.push({
          document_id: doc.id,
          document_type: doc.type,
          document_path: doc.path,
          similarity,
          metadata: doc.metadata,
          excerpt: this.generateExcerpt(doc.content.text, 200)
        });
      }
    }
    
    return results
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, limit);
  }

  async performKeywordSearch(query, documents, limit) {
    const queryWords = query.toLowerCase().split(/\s+/);
    const results = [];
    
    for (const doc of documents) {
      const content = doc.content.text.toLowerCase();
      let score = 0;
      
      for (const word of queryWords) {
        const occurrences = (content.match(new RegExp(word, 'g')) || []).length;
        score += occurrences;
      }
      
      if (score > 0) {
        results.push({
          document_id: doc.id,
          document_type: doc.type,
          document_path: doc.path,
          keyword_score: score,
          metadata: doc.metadata,
          excerpt: this.generateExcerpt(doc.content.text, 200)
        });
      }
    }
    
    return results
      .sort((a, b) => b.keyword_score - a.keyword_score)
      .slice(0, limit);
  }

  async performHybridSearch(query, documents, threshold, limit) {
    const semanticResults = await this.performSemanticSearch(
      await this.generateEmbeddings(query), 
      documents, 
      threshold, 
      limit * 2
    );
    
    const keywordResults = await this.performKeywordSearch(query, documents, limit * 2);
    
    // Combine and deduplicate results
    const combinedResults = new Map();
    
    // Add semantic results
    semanticResults.forEach(result => {
      combinedResults.set(result.document_id, {
        ...result,
        semantic_score: result.similarity,
        keyword_score: 0
      });
    });
    
    // Add keyword results and merge
    keywordResults.forEach(result => {
      if (combinedResults.has(result.document_id)) {
        const existing = combinedResults.get(result.document_id);
        existing.keyword_score = result.keyword_score;
        existing.hybrid_score = (existing.semantic_score * 0.6) + (result.keyword_score * 0.4);
      } else {
        combinedResults.set(result.document_id, {
          ...result,
          semantic_score: 0,
          keyword_score: result.keyword_score,
          hybrid_score: result.keyword_score * 0.4
        });
      }
    });
    
    return Array.from(combinedResults.values())
      .sort((a, b) => (b.hybrid_score || b.semantic_score || b.keyword_score) - (a.hybrid_score || a.semantic_score || a.keyword_score))
      .slice(0, limit);
  }

  calculateCosineSimilarity(vecA, vecB) {
    let dotProduct = 0;
    let normA = 0;
    let normB = 0;
    
    for (let i = 0; i < vecA.length; i++) {
      dotProduct += vecA[i] * vecB[i];
      normA += vecA[i] * vecA[i];
      normB += vecB[i] * vecB[i];
    }
    
    normA = Math.sqrt(normA);
    normB = Math.sqrt(normB);
    
    if (normA === 0 || normB === 0) return 0;
    
    return dotProduct / (normA * normB);
  }

  generateExcerpt(text, maxLength) {
    if (text.length <= maxLength) return text;
    
    const excerpt = text.substring(0, maxLength);
    const lastSpace = excerpt.lastIndexOf(' ');
    
    return lastSpace > 0 ? excerpt.substring(0, lastSpace) + '...' : excerpt + '...';
  }

  async extractParticipants(transcript) {
    // Simple participant extraction (in production, use speaker diarization)
    const lines = transcript.split('\n');
    const participants = new Map();
    
    for (const line of lines) {
      const match = line.match(/^(\w+):\s*(.+)$/);
      if (match) {
        const [, name, message] = match;
        if (!participants.has(name)) {
          participants.set(name, {
            name,
            messages: [],
            speaking_time: 0
          });
        }
        
        const participant = participants.get(name);
        participant.messages.push({
          content: message,
          timestamp: new Date().toISOString() // Mock timestamp
        });
        participant.speaking_time += message.length; // Mock speaking time
      }
    }
    
    return Array.from(participants.values());
  }

  async extractDecisions(transcript) {
    // Simple decision extraction (in production, use NLP)
    const decisionKeywords = ['decided', 'agreed', 'concluded', 'resolved', 'determined'];
    const lines = transcript.split('\n');
    const decisions = [];
    
    for (const line of lines) {
      for (const keyword of decisionKeywords) {
        if (line.toLowerCase().includes(keyword)) {
          decisions.push({
            text: line.trim(),
            confidence: 0.8,
            context: this.getContextAroundLine(lines, lines.indexOf(line))
          });
          break;
        }
      }
    }
    
    return decisions;
  }

  async extractActionItems(transcript) {
    // Simple action item extraction (in production, use NLP)
    const actionKeywords = ['action', 'task', 'todo', 'will', 'should', 'need to'];
    const lines = transcript.split('\n');
    const actionItems = [];
    
    for (const line of lines) {
      for (const keyword of actionKeywords) {
        if (line.toLowerCase().includes(keyword)) {
          actionItems.push({
            text: line.trim(),
            confidence: 0.7,
            assignee: this.extractAssignee(line),
            due_date: this.extractDueDate(line)
          });
          break;
        }
      }
    }
    
    return actionItems;
  }

  async generateMeetingSummary(transcript, analysis) {
    const summary = {
      duration: '1 hour', // Mock duration
      participant_count: analysis.participants?.length || 0,
      decisions_count: analysis.decisions?.length || 0,
      action_items_count: analysis.action_items?.length || 0,
      key_topics: this.extractKeyTopics(transcript),
      next_steps: analysis.action_items?.slice(0, 3) || []
    };
    
    return summary;
  }

  getContextAroundLine(lines, lineIndex, contextSize = 2) {
    const start = Math.max(0, lineIndex - contextSize);
    const end = Math.min(lines.length, lineIndex + contextSize + 1);
    
    return lines.slice(start, end).join('\n');
  }

  extractAssignee(line) {
    // Simple assignee extraction
    const match = line.match(/(\w+)\s+(?:will|should|needs? to)/);
    return match ? match[1] : null;
  }

  extractDueDate(line) {
    // Simple due date extraction
    const dateMatch = line.match(/\b\d{4}-\d{2}-\d{2}\b/);
    return dateMatch ? dateMatch[0] : null;
  }

  extractKeyTopics(transcript) {
    // Simple topic extraction (in production, use topic modeling)
    const commonWords = transcript.toLowerCase().split(/\s+/);
    const wordCounts = {};
    
    commonWords.forEach(word => {
      if (word.length > 4) { // Filter short words
        wordCounts[word] = (wordCounts[word] || 0) + 1;
      }
    });
    
    return Object.entries(wordCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([word]) => word);
  }

  async addDecisionRelationship(decisionId1, decisionId2) {
    // Mock relationship addition
    const relationshipKey = `rel:${decisionId1}:${decisionId2}`;
    this.knowledgeStore.set(relationshipKey, {
      type: 'decision_relationship',
      from: decisionId1,
      to: decisionId2,
      relationship_type: 'related_to',
      created_at: new Date().toISOString()
    });
  }

  async addKnowledgeEntity(entityData) {
    const entity = {
      ...entityData,
      created_at: new Date().toISOString()
    };
    
    this.knowledgeStore.set(`entity:${entityData.id}`, entity);
    
    return { message: 'Entity added successfully', entity_id: entityData.id };
  }

  async addKnowledgeRelationship(relationshipData) {
    const relationship = {
      ...relationshipData,
      created_at: new Date().toISOString()
    };
    
    const relationshipKey = `rel:${relationshipData.from_entity}:${relationshipData.to_entity}`;
    this.knowledgeStore.set(relationshipKey, relationship);
    
    return { message: 'Relationship added successfully', relationship_key: relationshipKey };
  }

  async queryKnowledgeGraph(query) {
    // Mock graph query
    const results = [];
    
    // Find entities matching query
    for (const [key, value] of this.knowledgeStore.entries()) {
      if (key.startsWith('entity:') && this.matchesQuery(value, query)) {
        results.push(value);
      }
    }
    
    return { results, query };
  }

  async getGraphContext(query) {
    // Mock context retrieval
    return {
      central_entity: query.entity_id,
      related_entities: [],
      context_paths: []
    };
  }

  matchesQuery(entity, query) {
    // Simple query matching
    if (query.name && entity.name && entity.name.includes(query.name)) {
      return true;
    }
    if (query.type && entity.type === query.type) {
      return true;
    }
    return false;
  }

  async getHistoricalDecisions(topic, timeRange) {
    // Mock historical decisions retrieval
    return {
      decisions: [],
      time_range: timeRange,
      topic_filter: topic
    };
  }

  async getRelatedDocuments(topic, timeRange) {
    // Mock related documents retrieval
    return {
      documents: [],
      relevance_scores: [],
      time_range: timeRange
    };
  }

  async getExpertiseAreas(topic) {
    // Mock expertise areas retrieval
    return {
      expertise_areas: [],
      experts: [],
      confidence_scores: []
    };
  }

  async getRecentChanges(topic, timeRange) {
    // Mock recent changes retrieval
    return {
      changes: [],
      change_types: [],
      impact_assessment: [],
      time_range: timeRange
    };
  }

  async getGeneralContext(topic) {
    // Mock general context retrieval
    return {
      overview: '',
      key_points: [],
      related_concepts: [],
      additional_resources: []
    };
  }

  async getRelatedTopics(topic) {
    // Mock related topics retrieval
    return [
      { topic: 'related1', relevance: 0.8 },
      { topic: 'related2', relevance: 0.6 },
      { topic: 'related3', relevance: 0.4 }
    ];
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Knowledge Base MCP server running on stdio');
  }
}

// Run the server
if (require.main === module) {
  const server = new KnowledgeBaseServer();
  server.run().catch(console.error);
}

module.exports = KnowledgeBaseServer;
