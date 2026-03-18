"""
Main entry point for Open SWE Gateway service
"""

import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

from .webhook_handlers import app as webhook_app
from .sandbox_manager import SandboxManager, run_cleanup_loop
from .deep_agents_bridge import DeepAgentsBridge
from .middleware_system import create_default_middleware_pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
sandbox_manager = None
deep_agents_bridge = None
middleware_pipeline = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""

    global sandbox_manager, deep_agents_bridge, middleware_pipeline

    # Startup
    logger.info("Starting Open SWE Gateway service")

    try:
        # Initialize components
        sandbox_manager = SandboxManager()
        deep_agents_bridge = DeepAgentsBridge()

        # Create middleware pipeline (with mock clients for now)
        middleware_pipeline = create_default_middleware_pipeline(
            gitops_client=None,  # TODO: Implement GitOps client
            risk_engine=None,    # TODO: Implement risk engine
            message_queue=None,  # TODO: Implement message queue
            git_client=None,     # TODO: Implement Git client
            pr_creator=None      # TODO: Implement PR creator
        )

        # Start background cleanup task
        cleanup_task = asyncio.create_task(run_cleanup_loop(sandbox_manager))

        logger.info("Open SWE Gateway service started successfully")

        yield

    except Exception as e:
        logger.error(f"Failed to start Open SWE Gateway service: {str(e)}")
        raise

    finally:
        # Shutdown
        logger.info("Shutting down Open SWE Gateway service")

        # Cancel cleanup task
        if 'cleanup_task' in locals():
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Open SWE Gateway service shutdown complete")

# Create main application
app = FastAPI(
    title="Open SWE Gateway",
    description="Bridge between Open SWE interactive triggers and GitOps control plane",
    version="1.0.0",
    lifespan=lifespan
)

# Mount webhook handlers
app.mount("/api/v1", webhook_app)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Open SWE Gateway",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Detailed health check"""

    # Check component health
    components = {
        "sandbox_manager": sandbox_manager is not None,
        "deep_agents_bridge": deep_agents_bridge is not None,
        "middleware_pipeline": middleware_pipeline is not None
    }

    all_healthy = all(components.values())

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "components": components,
        "active_sandboxes": len(sandbox_manager.active_sandboxes) if sandbox_manager else 0,
        "active_agents": len(deep_agents_bridge.active_agents) if deep_agents_bridge else 0
    }

# Global instances for webhook handlers to access
def get_sandbox_manager() -> SandboxManager:
    """Get sandbox manager instance"""
    return sandbox_manager

def get_deep_agents_bridge() -> DeepAgentsBridge:
    """Get Deep Agents bridge instance"""
    return deep_agents_bridge

def get_middleware_pipeline():
    """Get middleware pipeline instance"""
    return middleware_pipeline

# Update webhook handlers with service access
webhook_app.state.sandbox_manager = get_sandbox_manager
webhook_app.state.deep_agents_bridge = get_deep_agents_bridge
webhook_app.state.middleware_pipeline = get_middleware_pipeline

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
