"""
Unified Gateway for Open SWE Integration

This module provides the central entry point for all agent requests, implementing
intelligent routing, load balancing, and cross-platform request handling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Callable, Awaitable
from enum import Enum
import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class GatewayStatus(Enum):
    """Gateway operational status"""
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"
    IP_HASH = "ip_hash"


@dataclass
class BackendService:
    """Backend service endpoint"""
    id: str
    url: str
    weight: int = 1
    healthy: bool = True
    active_connections: int = 0
    total_requests: int = 0
    error_count: int = 0
    last_health_check: float = 0
    response_time: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteRule:
    """Routing rule for requests"""
    id: str
    pattern: str  # Regex pattern or simple string match
    priority: int = 1
    conditions: Dict[str, Any] = field(default_factory=dict)
    target_service: str = ""
    target_skill: str = ""
    transformation: Optional[Callable] = None
    enabled: bool = True


@dataclass
class GatewayRequest:
    """Request processed by gateway"""
    id: str
    platform: str
    method: str
    path: str
    headers: Dict[str, str]
    body: Any
    query_params: Dict[str, List[str]]
    client_ip: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GatewayResponse:
    """Response from gateway"""
    status_code: int
    headers: Dict[str, str]
    body: Any
    processing_time: float
    backend_service: Optional[str] = None
    error_message: Optional[str] = None


class HealthChecker(ABC):
    """Abstract health checker for backend services"""

    @abstractmethod
    async def check_health(self, service: BackendService) -> bool:
        """Check if service is healthy"""
        pass


class HTTPHealthChecker(HealthChecker):
    """HTTP-based health checker"""

    def __init__(self, timeout: float = 5.0, expected_status: int = 200):
        self.timeout = timeout
        self.expected_status = expected_status

    async def check_health(self, service: BackendService) -> bool:
        """Check service health via HTTP"""
        try:
            import aiohttp

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                start_time = time.time()
                async with session.get(f"{service.url}/health") as response:
                    response_time = time.time() - start_time
                    service.response_time = response_time
                    return response.status == self.expected_status

        except Exception as e:
            logger.warning(f"Health check failed for {service.url}: {e}")
            return False


class LoadBalancer:
    """Load balancer for backend services"""

    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.services: Dict[str, List[BackendService]] = defaultdict(list)
        self.round_robin_index: Dict[str, int] = defaultdict(int)
        self.ip_hash_cache: Dict[str, BackendService] = {}

    def add_service(self, service_type: str, service: BackendService):
        """Add service to load balancer"""
        self.services[service_type].append(service)

    def remove_service(self, service_type: str, service_id: str):
        """Remove service from load balancer"""
        self.services[service_type] = [
            s for s in self.services[service_type] if s.id != service_id
        ]

    def get_service(self, service_type: str, request: GatewayRequest = None) -> Optional[BackendService]:
        """Get next service using load balancing strategy"""
        available_services = [s for s in self.services[service_type] if s.healthy]

        if not available_services:
            return None

        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin(service_type, available_services)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections(available_services)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin(service_type, available_services)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random(available_services)
        elif self.strategy == LoadBalancingStrategy.IP_HASH:
            return self._ip_hash(request, available_services)
        else:
            return available_services[0]

    def _round_robin(self, service_type: str, services: List[BackendService]) -> BackendService:
        """Round-robin load balancing"""
        index = self.round_robin_index[service_type]
        service = services[index % len(services)]
        self.round_robin_index[service_type] = (index + 1) % len(services)
        return service

    def _least_connections(self, services: List[BackendService]) -> BackendService:
        """Least connections load balancing"""
        return min(services, key=lambda s: s.active_connections)

    def _weighted_round_robin(self, service_type: str, services: List[BackendService]) -> BackendService:
        """Weighted round-robin load balancing"""
        total_weight = sum(s.weight for s in services)
        current_weight = self.round_robin_index[service_type]

        for service in services:
            current_weight -= service.weight
            if current_weight <= 0:
                self.round_robin_index[service_type] = (current_weight + total_weight) % total_weight
                return service

        return services[0]

    def _random(self, services: List[BackendService]) -> BackendService:
        """Random load balancing"""
        import random
        return random.choice(services)

    def _ip_hash(self, request: GatewayRequest, services: List[BackendService]) -> BackendService:
        """IP hash load balancing"""
        if not request:
            return services[0]

        ip = request.client_ip
        if ip in self.ip_hash_cache:
            return self.ip_hash_cache[ip]

        hash_value = int(hashlib.md5(ip.encode()).hexdigest(), 16)
        service = services[hash_value % len(services)]
        self.ip_hash_cache[ip] = service
        return service


class RequestRouter:
    """Intelligent request router"""

    def __init__(self):
        self.routes: List[RouteRule] = []
        self.skill_mappings: Dict[str, str] = {}
        self.platform_mappings: Dict[str, str] = {}

    def add_route(self, route: RouteRule):
        """Add routing rule"""
        self.routes.append(route)
        self.routes.sort(key=lambda r: r.priority, reverse=True)

    def remove_route(self, route_id: str):
        """Remove routing rule"""
        self.routes = [r for r in self.routes if r.id != route_id]

    def route_request(self, request: GatewayRequest) -> Tuple[Optional[str], Optional[str]]:
        """Route request to appropriate service and skill"""
        for route in self.routes:
            if not route.enabled:
                continue

            if self._matches_route(request, route):
                return route.target_service, route.target_skill

        # Default routing based on platform
        return self._default_routing(request)

    def _matches_route(self, request: GatewayRequest, route: RouteRule) -> bool:
        """Check if request matches route"""
        import re

        # Check path pattern
        if not re.match(route.pattern, request.path):
            return False

        # Check conditions
        for key, expected_value in route.conditions.items():
            actual_value = request.metadata.get(key) or getattr(request, key, None)
            if actual_value != expected_value:
                return False

        return True

    def _default_routing(self, request: GatewayRequest) -> Tuple[Optional[str], Optional[str]]:
        """Default routing logic"""
        platform = request.metadata.get('platform', request.platform)

        # Route based on platform
        if platform == 'slack':
            return 'slack-agent', 'general-assistant'
        elif platform == 'github':
            return 'github-agent', 'pr-reviewer'
        elif platform == 'linear':
            return 'linear-agent', 'issue-manager'
        else:
            return 'general-agent', 'general-assistant'

    def update_skill_mapping(self, skill_name: str, service_id: str):
        """Update skill to service mapping"""
        self.skill_mappings[skill_name] = service_id

    def get_skill_service(self, skill_name: str) -> Optional[str]:
        """Get service for skill"""
        return self.skill_mappings.get(skill_name)


class CircuitBreaker:
    """Circuit breaker for fault tolerance"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count: Dict[str, int] = {}
        self.last_failure_time: Dict[str, float] = {}
        self.state: Dict[str, str] = defaultdict(lambda: "closed")  # closed, open, half_open

    def can_execute(self, service_id: str) -> bool:
        """Check if service can be executed"""
        state = self.state[service_id]

        if state == "closed":
            return True
        elif state == "open":
            if time.time() - self.last_failure_time.get(service_id, 0) > self.recovery_timeout:
                self.state[service_id] = "half_open"
                return True
            return False
        elif state == "half_open":
            return True

        return False

    def record_success(self, service_id: str):
        """Record successful execution"""
        self.failure_count[service_id] = 0
        self.state[service_id] = "closed"

    def record_failure(self, service_id: str):
        """Record failed execution"""
        self.failure_count[service_id] = self.failure_count.get(service_id, 0) + 1
        self.last_failure_time[service_id] = time.time()

        if self.failure_count[service_id] >= self.failure_threshold:
            self.state[service_id] = "open"


class RequestProcessor:
    """Processes requests through the gateway"""

    def __init__(self, load_balancer: LoadBalancer, router: RequestRouter,
                 circuit_breaker: CircuitBreaker):
        self.load_balancer = load_balancer
        self.router = router
        self.circuit_breaker = circuit_breaker
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.processing_workers: List[asyncio.Task] = []

    async def start_processing(self, num_workers: int = 4):
        """Start request processing workers"""
        for i in range(num_workers):
            worker = asyncio.create_task(self._process_requests())
            self.processing_workers.append(worker)

    async def stop_processing(self):
        """Stop request processing"""
        for worker in self.processing_workers:
            worker.cancel()
        await asyncio.gather(*self.processing_workers, return_exceptions=True)

    async def submit_request(self, request: GatewayRequest) -> asyncio.Future:
        """Submit request for processing"""
        future = asyncio.Future()
        await self.request_queue.put((request, future))
        return future

    async def _process_requests(self):
        """Process requests from queue"""
        while True:
            try:
                request, future = await self.request_queue.get()

                try:
                    response = await self._handle_request(request)
                    future.set_result(response)
                except Exception as e:
                    future.set_exception(e)

                self.request_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing request: {e}")

    async def _handle_request(self, request: GatewayRequest) -> GatewayResponse:
        """Handle individual request"""
        start_time = time.time()

        try:
            # Route request
            service_type, skill_name = self.router.route_request(request)

            if not service_type:
                return GatewayResponse(
                    status_code=404,
                    headers={},
                    body={"error": "No route found for request"},
                    processing_time=time.time() - start_time
                )

            # Get backend service
            backend_service = self.load_balancer.get_service(service_type, request)

            if not backend_service:
                return GatewayResponse(
                    status_code=503,
                    headers={},
                    body={"error": "No healthy backend services available"},
                    processing_time=time.time() - start_time
                )

            # Check circuit breaker
            if not self.circuit_breaker.can_execute(backend_service.id):
                return GatewayResponse(
                    status_code=503,
                    headers={},
                    body={"error": "Service temporarily unavailable"},
                    processing_time=time.time() - start_time
                )

            # Forward request to backend
            response = await self._forward_to_backend(request, backend_service)

            # Record success
            self.circuit_breaker.record_success(backend_service.id)
            backend_service.total_requests += 1

            return response

        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            return GatewayResponse(
                status_code=500,
                headers={},
                body={"error": "Internal server error"},
                processing_time=time.time() - start_time,
                error_message=str(e)
            )

    async def _forward_to_backend(self, request: GatewayRequest, service: BackendService) -> GatewayResponse:
        """Forward request to backend service"""
        try:
            import aiohttp

            service.active_connections += 1

            async with aiohttp.ClientSession() as session:
                # Prepare request data
                url = f"{service.url}{request.path}"
                headers = dict(request.headers)
                headers.update({
                    "X-Gateway-Request-ID": request.id,
                    "X-Gateway-Platform": request.platform,
                    "X-Client-IP": request.client_ip
                })

                # Forward request
                async with session.request(
                    method=request.method,
                    url=url,
                    headers=headers,
                    data=request.body,
                    params=request.query_params
                ) as response:
                    response_body = await response.read()
                    response_headers = dict(response.headers)

                    service.active_connections -= 1

                    return GatewayResponse(
                        status_code=response.status,
                        headers=response_headers,
                        body=response_body,
                        processing_time=time.time() - request.timestamp,
                        backend_service=service.id
                    )

        except Exception as e:
            service.active_connections -= 1
            self.circuit_breaker.record_failure(service.id)
            raise


class UnifiedGateway:
    """Main unified gateway class"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.status = GatewayStatus.INITIALIZING

        # Core components
        self.load_balancer = LoadBalancer(
            strategy=LoadBalancingStrategy(config.get("load_balancing_strategy", "round_robin"))
        )
        self.router = RequestRouter()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.get("circuit_breaker_failure_threshold", 5),
            recovery_timeout=config.get("circuit_breaker_recovery_timeout", 60.0)
        )
        self.processor = RequestProcessor(
            self.load_balancer,
            self.router,
            self.circuit_breaker
        )

        # Health checking
        self.health_checker = HTTPHealthChecker()
        self.health_check_interval = config.get("health_check_interval", 30.0)
        self.health_check_task: Optional[asyncio.Task] = None

        # Metrics and monitoring
        self.metrics: Dict[str, Any] = defaultdict(int)

    async def start(self):
        """Start the gateway"""
        logger.info("Starting Unified Gateway")

        # Initialize backend services
        await self._initialize_services()

        # Setup routing rules
        await self._setup_routing()

        # Start request processing
        await self.processor.start_processing(
            num_workers=self.config.get("processing_workers", 4)
        )

        # Start health checking
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        self.status = GatewayStatus.HEALTHY
        logger.info("Unified Gateway started successfully")

    async def stop(self):
        """Stop the gateway"""
        logger.info("Stopping Unified Gateway")

        self.status = GatewayStatus.UNHEALTHY

        # Stop health checking
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        # Stop request processing
        await self.processor.stop_processing()

        logger.info("Unified Gateway stopped")

    async def handle_request(self, request: GatewayRequest) -> GatewayResponse:
        """Handle incoming request"""
        if self.status != GatewayStatus.HEALTHY:
            return GatewayResponse(
                status_code=503,
                headers={},
                body={"error": "Gateway not ready"},
                processing_time=0
            )

        # Submit request for processing
        future = await self.processor.submit_request(request)
        response = await future

        # Update metrics
        self._update_metrics(request, response)

        return response

    async def _initialize_services(self):
        """Initialize backend services"""
        services_config = self.config.get("backend_services", {})

        for service_type, services in services_config.items():
            for service_config in services:
                service = BackendService(
                    id=service_config["id"],
                    url=service_config["url"],
                    weight=service_config.get("weight", 1),
                    metadata=service_config.get("metadata", {})
                )
                self.load_balancer.add_service(service_type, service)

        logger.info(f"Initialized {sum(len(s) for s in self.load_balancer.services.values())} backend services")

    async def _setup_routing(self):
        """Setup routing rules"""
        routing_config = self.config.get("routing", {})

        # Add route rules
        for route_config in routing_config.get("rules", []):
            route = RouteRule(
                id=route_config["id"],
                pattern=route_config["pattern"],
                priority=route_config.get("priority", 1),
                conditions=route_config.get("conditions", {}),
                target_service=route_config.get("target_service", ""),
                target_skill=route_config.get("target_skill", ""),
                enabled=route_config.get("enabled", True)
            )
            self.router.add_route(route)

        # Setup skill mappings
        for skill, service in routing_config.get("skill_mappings", {}).items():
            self.router.update_skill_mapping(skill, service)

        logger.info(f"Setup {len(self.router.routes)} routing rules")

    async def _health_check_loop(self):
        """Periodic health checking of backend services"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)

                for service_type, services in self.load_balancer.services.items():
                    for service in services:
                        healthy = await self.health_checker.check_health(service)
                        service.healthy = healthy
                        service.last_health_check = time.time()

                        if not healthy:
                            logger.warning(f"Service {service.id} is unhealthy")

                # Update gateway status based on service health
                total_services = sum(len(s) for s in self.load_balancer.services.values())
                healthy_services = sum(
                    len([s for s in services if s.healthy])
                    for services in self.load_balancer.services.values()
                )

                if healthy_services == 0:
                    self.status = GatewayStatus.UNHEALTHY
                elif healthy_services < total_services:
                    self.status = GatewayStatus.DEGRADED
                else:
                    self.status = GatewayStatus.HEALTHY

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")

    def _update_metrics(self, request: GatewayRequest, response: GatewayResponse):
        """Update gateway metrics"""
        self.metrics["total_requests"] += 1
        self.metrics[f"status_{response.status_code}"] += 1
        self.metrics["avg_processing_time"] = (
            (self.metrics.get("avg_processing_time", 0) * (self.metrics["total_requests"] - 1) +
             response.processing_time) / self.metrics["total_requests"]
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get gateway metrics"""
        return dict(self.metrics)

    def get_status(self) -> GatewayStatus:
        """Get gateway status"""
        return self.status

    def get_service_status(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get status of all backend services"""
        status = {}
        for service_type, services in self.load_balancer.services.items():
            status[service_type] = [
                {
                    "id": s.id,
                    "url": s.url,
                    "healthy": s.healthy,
                    "active_connections": s.active_connections,
                    "total_requests": s.total_requests,
                    "response_time": s.response_time
                }
                for s in services
            ]
        return status


# Export key classes
__all__ = [
    'GatewayStatus',
    'LoadBalancingStrategy',
    'BackendService',
    'RouteRule',
    'GatewayRequest',
    'GatewayResponse',
    'HealthChecker',
    'HTTPHealthChecker',
    'LoadBalancer',
    'RequestRouter',
    'CircuitBreaker',
    'RequestProcessor',
    'UnifiedGateway'
]
