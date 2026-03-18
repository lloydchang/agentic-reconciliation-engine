"""
Open SWE Gateway Service
Bridge between Open SWE interactive triggers and GitOps control plane
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
import hmac
import hashlib
import json
import logging
from datetime import datetime

app = FastAPI(title="Open SWE Gateway", version="1.0.0")
logger = logging.getLogger(__name__)

# Models
class SlackWebhookRequest(BaseModel):
    token: str
    team_id: str
    api_app_id: str
    event: Dict[str, Any]
    type: str
    event_id: str
    event_time: int

class LinearWebhookRequest(BaseModel):
    action: str
    data: Dict[str, Any]
    type: str
    organizationId: str

class GitHubWebhookRequest(BaseModel):
    action: str
    issue: Optional[Dict[str, Any]] = None
    comment: Optional[Dict[str, Any]] = None
    repository: Dict[str, Any]
    sender: Dict[str, Any]

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    estimated_completion: Optional[str] = None

# Webhook Handlers
@app.post("/webhooks/slack", response_model=TaskResponse)
async def slack_webhook(request: SlackWebhookRequest, req: Request):
    """Process Slack bot mentions and thread replies"""

    # Basic validation (implement proper signature verification)
    if not validate_slack_request(req):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")

    # Extract bot mention and context
    event = request.event
    if event.get("type") == "app_mention":
        text = event.get("text", "")
        channel = event.get("channel")
        user = event.get("user")
        thread_ts = event.get("thread_ts")

        # Route to GitOps agent
        task_id = await route_slack_request(text, channel, user, thread_ts)

        return TaskResponse(
            task_id=task_id,
            status="accepted",
            message="Task accepted and queued for processing",
            estimated_completion="TBD"
        )

    return TaskResponse(
        task_id="",
        status="ignored",
        message="Event type not supported"
    )

@app.post("/webhooks/linear", response_model=TaskResponse)
async def linear_webhook(request: LinearWebhookRequest):
    """Process Linear issue comments and mentions"""

    if request.type == "Comment" and "@openswe" in request.data.get("body", ""):
        issue_data = request.data.get("issue", {})
        comment_body = request.data.get("body", "")

        # Route to GitOps agent
        task_id = await route_linear_request(issue_data, comment_body)

        return TaskResponse(
            task_id=task_id,
            status="accepted",
            message="Linear issue processing started"
        )

    return TaskResponse(
        task_id="",
        status="ignored",
        message="Not a relevant Linear event"
    )

@app.post("/webhooks/github", response_model=TaskResponse)
async def github_webhook(request: GitHubWebhookRequest, req: Request):
    """Process GitHub issue and PR events"""

    # Validate GitHub webhook signature
    if not validate_github_signature(req):
        raise HTTPException(status_code=401, detail="Invalid GitHub signature")

    if request.action in ["opened", "edited"] and request.comment:
        comment_body = request.comment.get("body", "")
        if "@openswe" in comment_body:
            # Route to GitOps agent
            task_id = await route_github_request(request, comment_body)

            return TaskResponse(
                task_id=task_id,
                status="accepted",
                message="GitHub comment processing started"
            )

    return TaskResponse(
        task_id="",
        status="ignored",
        message="Not a relevant GitHub event"
    )

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get real-time task status and progress"""
    # Query Temporal workflow status
    status = await get_temporal_workflow_status(task_id)

    return {
        "task_id": task_id,
        "status": status.get("status", "unknown"),
        "progress": status.get("progress", {}),
        "messages": status.get("messages", []),
        "last_updated": datetime.utcnow().isoformat()
    }

@app.post("/messages/{task_id}")
async def inject_message(task_id: str, message: str):
    """Inject user message into running task"""
    success = await inject_message_into_workflow(task_id, message)

    if success:
        return {"status": "message_injected", "task_id": task_id}
    else:
        raise HTTPException(status_code=404, detail="Task not found or not running")

# Helper Functions
async def validate_slack_request(request: Request) -> bool:
    """Validate Slack webhook signature"""
    # Implement proper Slack signature validation
    return True  # Placeholder

async def validate_github_signature(request: Request) -> bool:
    """Validate GitHub webhook signature"""
    # Implement proper GitHub signature validation
    return True  # Placeholder

async def route_slack_request(text: str, channel: str, user: str, thread_ts: str) -> str:
    """Route Slack request to appropriate GitOps agent"""
    # Implement routing logic to Temporal/GitOps
    return f"slack-{thread_ts or 'new'}-{datetime.utcnow().timestamp()}"

async def route_linear_request(issue_data: dict, comment_body: str) -> str:
    """Route Linear request to GitOps agent"""
    return f"linear-{issue_data.get('id', 'unknown')}-{datetime.utcnow().timestamp()}"

async def route_github_request(request: GitHubWebhookRequest, comment_body: str) -> str:
    """Route GitHub request to GitOps agent"""
    return f"github-{request.issue.get('number', 'unknown')}-{datetime.utcnow().timestamp()}"

async def get_temporal_workflow_status(task_id: str) -> dict:
    """Query Temporal workflow status"""
    # Implement Temporal client integration
    return {"status": "running", "progress": {}}

async def inject_message_into_workflow(task_id: str, message: str) -> bool:
    """Inject message into running Temporal workflow"""
    # Implement message injection logic
    return True

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
