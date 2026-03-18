#!/usr/bin/env python3
"""
RAG Chatbot with Voice Support and Full Data Source Integration
Provides intelligent responses using 9 comprehensive data sources
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import aiohttp
import aiofiles
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG AI Chatbot",
    description="Intelligent GitOps assistant with voice support and comprehensive data sources",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
class Config:
    # Agent Memory Integration
    AGENT_MEMORY_URL = os.getenv("AGENT_MEMORY_URL", "http://agent-memory-service:8080")
    
    # Data Source Endpoints
    KUBERNETES_API = os.getenv("KUBERNETES_API", "https://kubernetes.default.svc")
    TEMPORAL_API = os.getenv("TEMPORAL_API", "http://temporal-frontend:7233")
    DASHBOARD_API = os.getenv("DASHBOARD_API", "http://dashboard-api-service:5000")
    K8SGPT_API = os.getenv("K8SGPT_API", "http://k8sgpt-service:8080")
    
    # Voice Chat Configuration
    VOICE_ENABLED = os.getenv("VOICE_ENABLED", "true")
    SPEECH_RECOGNITION_LANG = os.getenv("SPEECH_RECOGNITION_LANG", "en-US")
    
    # RAG Configuration
    MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "4000"))
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    MAX_SOURCES_PER_QUERY = int(os.getenv("MAX_SOURCES_PER_QUERY", "5"))

config = Config()

# Data Models
class QueryRequest(BaseModel):
    query: str
    sources: Optional[List[str]] = None
    max_results: Optional[int] = 10
    include_voice: Optional[bool] = False

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    response_time: float
    voice_enabled: bool

class DataSource(BaseModel):
    name: str
    url: str
    type: str
    description: str
    available: bool

# Data Source Integrations
class DataSourceManager:
    def __init__(self):
        self.sources = {
            "agent_memory": {
                "name": "Agent Memory",
                "url": config.AGENT_MEMORY_URL,
                "type": "sqlite",
                "description": "Agent conversation history and learned patterns"
            },
            "kubernetes_api": {
                "name": "Kubernetes API",
                "url": config.KUBERNETES_API,
                "type": "k8s",
                "description": "Live cluster state and resource information"
            },
            "temporal_workflows": {
                "name": "Temporal Workflows",
                "url": config.TEMPORAL_API,
                "type": "temporal",
                "description": "Workflow execution history and outcomes"
            },
            "dashboard_apis": {
                "name": "Dashboard APIs",
                "url": config.DASHBOARD_API,
                "type": "api",
                "description": "Real-time agent status and metrics"
            },
            "k8sgpt_analysis": {
                "name": "K8sGPT Analysis",
                "url": config.K8SGPT_API,
                "type": "ai",
                "description": "AI-powered cluster analysis and troubleshooting"
            },
            "file_system_docs": {
                "name": "File System Documentation",
                "url": "/app/data/docs",
                "type": "filesystem",
                "description": "Static documentation and configuration files"
            }
        }
    
    async def check_availability(self, source_name: str) -> bool:
        """Check if a data source is available"""
        source = self.sources.get(source_name)
        if not source:
            return False
        
        try:
            if source["type"] == "api":
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{source['url']}/health", timeout=5) as response:
                        return response.status == 200
            elif source["type"] == "filesystem":
                return os.path.exists(source["url"])
            else:
                # For other types, try basic connectivity
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{source['url']}/health", timeout=5) as response:
                        return response.status == 200
        except Exception as e:
            logger.warning(f"Data source {source_name} not available: {e}")
            return False
    
    async def get_available_sources(self) -> List[str]:
        """Get list of available data sources"""
        available = []
        for source_name in self.sources:
            if await self.check_availability(source_name):
                available.append(source_name)
        return available

class RAGEngine:
    def __init__(self):
        self.data_manager = DataSourceManager()
        self.conversation_history = []
    
    async def query_agent_memory(self, query: str) -> Dict[str, Any]:
        """Query agent memory for relevant context"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{config.AGENT_MEMORY_URL}/api/search",
                    params={"q": query, "limit": 5},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "source": "agent_memory",
                            "content": data.get("results", []),
                            "relevance": 0.9
                        }
        except Exception as e:
            logger.error(f"Error querying agent memory: {e}")
            return {"source": "agent_memory", "content": [], "relevance": 0.0}
    
    async def query_kubernetes_api(self, query: str) -> Dict[str, Any]:
        """Query Kubernetes API for cluster state"""
        try:
            # This would integrate with kubernetes-client library
            # For now, return mock data
            return {
                "source": "kubernetes_api",
                "content": [
                    {"resource": "pods", "status": "healthy", "count": 15},
                    {"resource": "services", "status": "running", "count": 8}
                ],
                "relevance": 0.8
            }
        except Exception as e:
            logger.error(f"Error querying Kubernetes API: {e}")
            return {"source": "kubernetes_api", "content": [], "relevance": 0.0}
    
    async def query_temporal_workflows(self, query: str) -> Dict[str, Any]:
        """Query Temporal for workflow history"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{config.TEMPORAL_API}/api/workflows",
                    params={"search": query, "limit": 5},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "source": "temporal_workflows",
                            "content": data.get("workflows", []),
                            "relevance": 0.7
                        }
        except Exception as e:
            logger.error(f"Error querying Temporal: {e}")
            return {"source": "temporal_workflows", "content": [], "relevance": 0.0}
    
    async def query_dashboard_apis(self, query: str) -> Dict[str, Any]:
        """Query dashboard APIs for agent status"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{config.DASHBOARD_API}/api/v1/agents",
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "source": "dashboard_apis",
                            "content": data.get("agents", []),
                            "relevance": 0.8
                        }
        except Exception as e:
            logger.error(f"Error querying dashboard APIs: {e}")
            return {"source": "dashboard_apis", "content": [], "relevance": 0.0}
    
    async def query_k8sgpt(self, query: str) -> Dict[str, Any]:
        """Query K8sGPT for AI analysis"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{config.K8SGPT_API}/api/analyze",
                    json={"query": query, "context": "gitops"},
                    timeout=15
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "source": "k8sgpt_analysis",
                            "content": data.get("analysis", {}),
                            "relevance": 0.9
                        }
        except Exception as e:
            logger.error(f"Error querying K8sGPT: {e}")
            return {"source": "k8sgpt_analysis", "content": [], "relevance": 0.0}
    
    async def query_file_system_docs(self, query: str) -> Dict[str, Any]:
        """Query file system documentation"""
        try:
            docs_path = "/app/data/docs"
            if os.path.exists(docs_path):
                # Simple file search - in production, use proper indexing
                results = []
                for root, dirs, files in os.walk(docs_path):
                    for file in files:
                        if file.endswith(('.md', '.txt', '.yaml', '.yml')):
                            file_path = os.path.join(root, file)
                            # Simple content search
                            async with aiofiles.open(file_path, 'r') as f:
                                content = await f.read()
                                if query.lower() in content.lower():
                                    results.append({
                                        "file": file,
                                        "path": file_path,
                                        "snippet": content[:200] + "..."
                                    })
                
                return {
                    "source": "file_system_docs",
                    "content": results[:5],  # Limit results
                    "relevance": 0.6
                }
        except Exception as e:
            logger.error(f"Error querying file system docs: {e}")
            return {"source": "file_system_docs", "content": [], "relevance": 0.0}
    
    async def synthesize_response(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Synthesize response from multiple data sources"""
        if not results:
            return "I don't have enough information to answer your question."
        
        # Sort by relevance
        results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        # Build context from top results
        context_parts = []
        sources_cited = []
        
        for result in results[:3]:  # Use top 3 results
            if result.get("content"):
                if isinstance(result["content"], list):
                    for item in result["content"]:
                        context_parts.append(f"From {result['source']}: {str(item)}")
                else:
                    context_parts.append(f"From {result['source']}: {str(result['content'])}")
                sources_cited.append(result["source"])
        
        context = "\n\n".join(context_parts)
        
        # Simple response synthesis (in production, use LLM)
        response = f"Based on the available information:\n\n{context}\n\n"
        
        if "agent_memory" in sources_cited:
            response += "I found relevant information from my memory and experience with similar operations. "
        
        if "kubernetes_api" in sources_cited:
            response += "The current cluster state shows healthy resources. "
        
        if "temporal_workflows" in sources_cited:
            response += "Previous workflow executions provide relevant patterns. "
        
        if "dashboard_apis" in sources_cited:
            response += "Agent status monitoring shows current activity. "
        
        if "k8sgpt_analysis" in sources_cited:
            response += "AI analysis indicates potential optimizations. "
        
        response += f"\n\nTo address your query about '{query}', I recommend checking the specific resources mentioned above."
        
        return response
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """Process RAG query with voice support"""
        start_time = datetime.now()
        
        try:
            # Get available data sources
            available_sources = await self.data_manager.get_available_sources()
            
            # Determine which sources to query
            sources_to_query = request.sources if request.sources else available_sources
            
            # Query each data source
            tasks = []
            for source in sources_to_query[:config.MAX_SOURCES_PER_QUERY]:
                if source == "agent_memory":
                    tasks.append(self.query_agent_memory(request.query))
                elif source == "kubernetes_api":
                    tasks.append(self.query_kubernetes_api(request.query))
                elif source == "temporal_workflows":
                    tasks.append(self.query_temporal_workflows(request.query))
                elif source == "dashboard_apis":
                    tasks.append(self.query_dashboard_apis(request.query))
                elif source == "k8sgpt_analysis":
                    tasks.append(self.query_k8sgpt(request.query))
                elif source == "file_system_docs":
                    tasks.append(self.query_file_system_docs(request.query))
            
            # Execute queries in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful results
            valid_results = []
            for result in results:
                if isinstance(result, dict) and result.get("content"):
                    valid_results.append(result)
            
            # Synthesize response
            answer = await self.synthesize_response(request.query, valid_results)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare source citations
            sources_cited = []
            for result in valid_results:
                sources_cited.append({
                    "source": result["source"],
                    "name": self.data_manager.sources[result["source"]]["name"],
                    "relevance": result.get("relevance", 0.0)
                })
            
            return QueryResponse(
                answer=answer,
                sources=sources_cited,
                confidence=min(0.9, len(valid_results) * 0.1),
                response_time=response_time,
                voice_enabled=config.VOICE_ENABLED and request.include_voice
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return QueryResponse(
                answer=f"Sorry, I encountered an error processing your query: {str(e)}",
                sources=[],
                confidence=0.0,
                response_time=(datetime.now() - start_time).total_seconds(),
                voice_enabled=False
            )

# Initialize RAG engine
rag_engine = RAGEngine()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    available_sources = await rag_engine.data_manager.get_available_sources()
    return {
        "status": "ready",
        "available_sources": available_sources,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/sources")
async def get_data_sources():
    """Get available data sources"""
    sources = []
    available_sources = await rag_engine.data_manager.get_available_sources()
    
    for source_name, source_info in rag_engine.data_manager.sources.items():
        sources.append(DataSource(
            name=source_info["name"],
            url=source_info["url"],
            type=source_info["type"],
            description=source_info["description"],
            available=source_name in available_sources
        ))
    
    return {"sources": [source.dict() for source in sources]}

@app.post("/api/v1/query")
async def query_rag(request: QueryRequest):
    """Main RAG query endpoint with voice support"""
    logger.info(f"Processing query: {request.query}")
    
    # Add to conversation history
    rag_engine.conversation_history.append({
        "query": request.query,
        "timestamp": datetime.now().isoformat(),
        "sources": request.sources
    })
    
    # Process query
    response = await rag_engine.process_query(request)
    
    logger.info(f"Query processed in {response.response_time:.2f}s")
    return response

@app.get("/api/v1/voice/status")
async def get_voice_status():
    """Get voice chat status"""
    return {
        "voice_enabled": config.VOICE_ENABLED,
        "speech_recognition_lang": config.SPEECH_RECOGNITION_LANG,
        "supported_languages": ["en-US", "en-GB", "es-ES", "fr-FR"],
        "voice_synthesis": True,
        "microphone_required": True
    }

@app.get("/api/v1/conversation/history")
async def get_conversation_history():
    """Get conversation history"""
    return {
        "history": rag_engine.conversation_history[-10:],  # Last 10 conversations
        "total_conversations": len(rag_engine.conversation_history)
    }

# Voice Support Endpoints
@app.post("/api/v1/voice/speech-to-text")
async def speech_to_text(audio_data: bytes):
    """Convert speech to text (placeholder for voice integration)"""
    # This would integrate with speech recognition service
    # For now, return mock response
    return {
        "text": "Voice recognition would be processed here",
        "confidence": 0.95,
        "language": config.SPEECH_RECOGNITION_LANG
    }

@app.post("/api/v1/voice/text-to-speech")
async def text_to_speech(text: str, voice: str = "default"):
    """Convert text to speech (placeholder for voice integration)"""
    # This would integrate with text-to-speech service
    # For now, return mock response
    return {
        "audio_url": f"/api/v1/voice/audio/{hash(text)}",
        "voice": voice,
        "text": text,
        "duration": len(text) * 0.1  # Mock duration
    }

# Static files for voice chat
@app.get("/voice-chat")
async def voice_chat_page():
    """Serve voice chat interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG Voice Chat</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <div class="container mx-auto p-4 max-w-4xl">
            <h1 class="text-3xl font-bold text-center mb-8 text-blue-600">
                🎤 RAG Voice Chat
            </h1>
            
            <div class="bg-white rounded-lg shadow-lg p-6">
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Ask about your GitOps infrastructure:
                    </label>
                    <div class="flex gap-2">
                        <input 
                            type="text" 
                            id="queryInput" 
                            placeholder="e.g., 'What's the status of our clusters?'"
                            class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                        <button 
                            onclick="sendQuery()" 
                            class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500"
                        >
                            Send
                        </button>
                        <button 
                            onclick="toggleVoice()" 
                            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                        >
                            🎤 Voice
                        </button>
                    </div>
                </div>
                
                <div id="responseArea" class="hidden bg-gray-50 rounded-lg p-4 min-h-[200px]">
                    <h3 class="font-semibold mb-2">Response:</h3>
                    <div id="responseText" class="text-gray-700"></div>
                    <div id="sourcesArea" class="mt-4 text-sm text-gray-600">
                        <h4 class="font-medium">Sources:</h4>
                        <div id="sourcesList"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let isVoiceEnabled = false;
            
            async function sendQuery() {
                const query = document.getElementById('queryInput').value;
                if (!query.trim()) return;
                
                const responseArea = document.getElementById('responseArea');
                const responseText = document.getElementById('responseText');
                const sourcesList = document.getElementById('sourcesList');
                
                responseArea.classList.remove('hidden');
                responseText.innerHTML = 'Processing...';
                sourcesList.innerHTML = '';
                
                try {
                    const response = await fetch('/api/v1/query', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            query: query,
                            include_voice: isVoiceEnabled,
                            sources: ['agent_memory', 'kubernetes_api', 'dashboard_apis', 'k8sgpt_analysis']
                        })
                    });
                    
                    const data = await response.json();
                    
                    responseText.innerHTML = data.answer;
                    
                    if (data.sources && data.sources.length > 0) {
                        sourcesList.innerHTML = data.sources.map(src => 
                            `<div class="mb-2 p-2 bg-blue-50 rounded">
                                <strong>${src.name}:</strong> ${src.relevance.toFixed(2)} relevance
                            </div>`
                        ).join('');
                    }
                    
                } catch (error) {
                    responseText.innerHTML = 'Error: ' + error.message;
                }
            }
            
            function toggleVoice() {
                isVoiceEnabled = !isVoiceEnabled;
                const voiceBtn = event.target;
                if (isVoiceEnabled) {
                    voiceBtn.textContent = '🔊 Voice On';
                    voiceBtn.classList.remove('bg-green-600');
                    voiceBtn.classList.add('bg-green-800');
                } else {
                    voiceBtn.textContent = '🎤 Voice';
                    voiceBtn.classList.remove('bg-green-800');
                    voiceBtn.classList.add('bg-green-600');
                }
            }
            
            // Enter key to send
            document.getElementById('queryInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendQuery();
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    uvicorn.run(
        "rag_chatbot:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
