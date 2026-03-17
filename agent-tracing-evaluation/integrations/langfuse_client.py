#!/usr/bin/env python3
"""
Langfuse Integration Client
Connects to real Langfuse instance for trace data ingestion and evaluation
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

@dataclass
class LangfuseConfig:
    """Langfuse configuration"""
    api_key: str
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    batch_size: int = 1000
    enable_streaming: bool = True

@dataclass
class TraceFilter:
    """Filter criteria for Langfuse traces"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: Optional[List[str]] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = 1000
    offset: int = 0
    order_by: str = "timestamp"
    order_direction: str = "desc"

class LangfuseClient:
    """Real Langfuse integration client"""
    
    def __init__(self, config: LangfuseConfig):
        self.config = config
        self.session = self._create_session()
        self.base_url = config.base_url.rstrip('/')
        
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Agent-Evaluation-Framework/1.0'
        })
        
        return session
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request to Langfuse API"""
        url = f"{self.base_url}/api/public/{endpoint}"
        
        try:
            response = self.session.request(
                method, 
                url, 
                timeout=self.config.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Langfuse API request failed: {e}")
            raise
    
    def fetch_traces(self, filters: Optional[TraceFilter] = None) -> List[Dict[str, Any]]:
        """
        Fetch traces from Langfuse
        
        Args:
            filters: Optional filter criteria
            
        Returns:
            List of trace data
        """
        if filters is None:
            filters = TraceFilter()
        
        # Build query parameters
        params = {
            'limit': filters.limit,
            'offset': filters.offset,
            'orderBy': filters.order_by,
            'orderDirection': filters.order_direction
        }
        
        if filters.user_id:
            params['userId'] = filters.user_id
        if filters.session_id:
            params['sessionId'] = filters.session_id
        if filters.tags:
            params['tags'] = ','.join(filters.tags)
        if filters.from_date:
            params['fromDate'] = filters.from_date.isoformat()
        if filters.to_date:
            params['toDate'] = filters.to_date.isoformat()
        
        try:
            response = self._make_request('GET', 'traces', params=params)
            traces_data = response.json()
            
            # Convert Langfuse format to evaluation framework format
            evaluation_traces = self._convert_traces(traces_data.get('data', []))
            
            logger.info(f"Fetched {len(evaluation_traces)} traces from Langfuse")
            return evaluation_traces
            
        except Exception as e:
            logger.error(f"Failed to fetch traces from Langfuse: {e}")
            raise
    
    async def stream_traces(self, filters: Optional[TraceFilter] = None) -> Iterator[Dict[str, Any]]:
        """
        Stream traces from Langfuse in real-time
        
        Args:
            filters: Optional filter criteria
            
        Yields:
            Individual trace data
        """
        if not self.config.enable_streaming:
            raise ValueError("Streaming is not enabled in configuration")
        
        if filters is None:
            filters = TraceFilter(limit=100)  # Smaller batches for streaming
        
        logger.info("Starting real-time trace streaming from Langfuse")
        
        try:
            # Use Langfuse's streaming endpoint if available
            # For now, implement polling-based streaming
            last_timestamp = datetime.utcnow() - timedelta(minutes=5)
            
            while True:
                # Update filter to get only new traces
                filters.from_date = last_timestamp
                filters.limit = 50  # Small batch for real-time
                
                traces = self.fetch_traces(filters)
                
                if traces:
                    for trace in traces:
                        yield trace
                        # Update last timestamp
                        trace_time = datetime.fromisoformat(trace.get('timestamp', '').replace('Z', '+00:00'))
                        if trace_time > last_timestamp:
                            last_timestamp = trace_time
                
                # Wait before next poll
                await asyncio.sleep(10)  # Poll every 10 seconds
                
        except KeyboardInterrupt:
            logger.info("Trace streaming stopped by user")
        except Exception as e:
            logger.error(f"Error in trace streaming: {e}")
            raise
    
    def get_trace_by_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific trace by ID
        
        Args:
            trace_id: Unique trace identifier
            
        Returns:
            Trace data or None if not found
        """
        try:
            response = self._make_request('GET', f'traces/{trace_id}')
            trace_data = response.json()
            
            # Convert to evaluation format
            evaluation_trace = self._convert_traces([trace_data])[0]
            
            return evaluation_trace
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Trace {trace_id} not found")
                return None
            raise
    
    def _convert_traces(self, langfuse_traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert Langfuse trace format to evaluation framework format
        
        Args:
            langfuse_traces: Raw traces from Langfuse
            
        Returns:
            Converted traces for evaluation
        """
        evaluation_traces = []
        
        for lf_trace in langfuse_traces:
            try:
                # Extract basic trace information
                trace_id = lf_trace.get('id')
                timestamp = lf_trace.get('timestamp')
                user_id = lf_trace.get('userId')
                session_id = lf_trace.get('sessionId')
                tags = lf_trace.get('tags', [])
                metadata = lf_trace.get('metadata', {})
                
                # Extract observations (events)
                observations = lf_trace.get('observations', [])
                events = []
                
                for obs in observations:
                    event = {
                        'name': obs.get('name', 'unknown'),
                        'timestamp': obs.get('startTime'),
                        'duration': obs.get('duration'),
                        'level': obs.get('level', 'INFO'),
                        'type': obs.get('type', 'DEFAULT'),
                        'input': obs.get('input'),
                        'output': obs.get('output'),
                        'metadata': obs.get('metadata', {})
                    }
                    events.append(event)
                
                # Calculate trace metrics
                total_duration = sum(
                    obs.get('duration', 0) for obs in observations 
                    if obs.get('duration') is not None
                )
                
                error_count = sum(
                    1 for obs in observations 
                    if obs.get('level') == 'ERROR'
                )
                
                # Build evaluation trace
                evaluation_trace = {
                    'id': trace_id,
                    'timestamp': timestamp,
                    'user_id': user_id,
                    'session_id': session_id,
                    'tags': tags,
                    'events': events,
                    'attributes': {
                        'total_duration': total_duration,
                        'event_count': len(events),
                        'error_count': error_count,
                        'success_rate': (len(events) - error_count) / len(events) if events else 0,
                        'source': 'langfuse',
                        **metadata
                    },
                    'langfuse_metadata': {
                        'trace_id': trace_id,
                        'observations': observations,
                        'raw_trace': lf_trace
                    }
                }
                
                evaluation_traces.append(evaluation_trace)
                
            except Exception as e:
                logger.warning(f"Failed to convert Langfuse trace {lf_trace.get('id')}: {e}")
                continue
        
        return evaluation_traces
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check Langfuse service health
        
        Returns:
            Health status information
        """
        try:
            response = self._make_request('GET', 'health')
            health_data = response.json()
            
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'langfuse_status': health_data,
                'connection': True
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'connection': False
            }
    
    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()

class LangfuseTraceGenerator:
    """Generate evaluation traces from Langfuse data"""
    
    def __init__(self, client: LangfuseClient):
        self.client = client
    
    def generate_evaluation_traces(self, count: int = 100, 
                                  filters: Optional[TraceFilter] = None) -> List[Dict[str, Any]]:
        """
        Generate traces for evaluation from Langfuse
        
        Args:
            count: Number of traces to generate
            filters: Optional filter criteria
            
        Returns:
            List of traces for evaluation
        """
        if filters is None:
            filters = TraceFilter(limit=count)
        else:
            filters.limit = count
        
        logger.info(f"Generating {count} evaluation traces from Langfuse")
        
        try:
            traces = self.client.fetch_traces(filters)
            
            # If we need more traces, fetch in batches
            if len(traces) < count:
                remaining = count - len(traces)
                filters.offset = len(traces)
                
                while len(traces) < count and remaining > 0:
                    batch = self.client.fetch_traces(filters)
                    if not batch:
                        break
                    
                    traces.extend(batch)
                    filters.offset += len(batch)
                    remaining = count - len(traces)
            
            logger.info(f"Generated {len(traces)} evaluation traces")
            return traces[:count]
            
        except Exception as e:
            logger.error(f"Failed to generate evaluation traces from Langfuse: {e}")
            # Fallback to sample traces if Langfuse is unavailable
            logger.warning("Falling back to sample traces")
            from example_usage import generate_sample_traces
            return generate_sample_traces(count)

# Factory function
def create_langfuse_client() -> LangfuseClient:
    """Create Langfuse client from environment variables"""
    api_key = os.getenv('LANGFUSE_API_KEY')
    base_url = os.getenv('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')
    
    if not api_key:
        raise ValueError("LANGFUSE_API_KEY environment variable is required")
    
    config = LangfuseConfig(
        api_key=api_key,
        base_url=base_url,
        timeout=int(os.getenv('LANGFUSE_TIMEOUT', '30')),
        max_retries=int(os.getenv('LANGFUSE_MAX_RETRIES', '3')),
        batch_size=int(os.getenv('LANGFUSE_BATCH_SIZE', '1000')),
        enable_streaming=os.getenv('LANGFUSE_ENABLE_STREAMING', 'true').lower() == 'true'
    )
    
    return LangfuseClient(config)
