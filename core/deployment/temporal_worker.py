#!/usr/bin/env python3
"""
Temporal Worker for AI Agent Evaluation Framework

Handles evaluation workflows and activities in Temporal.
"""

import asyncio
import logging
import os
import sys
from datetime import timedelta
from pathlib import Path

from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.common import RetryPolicy

# Add framework to path
sys.path.append(str(Path(__file__).parent / "agent-tracing-evaluation"))

from main import TracingEvaluationFramework
from visualization import EvaluationVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global framework instances
evaluation_framework = TracingEvaluationFramework()
visualizer = EvaluationVisualizer()

# Temporal task queue
TASK_QUEUE = "ai-agent-evaluation"

@activity.defn
async def prepare_evaluation_environment(input_data: dict) -> dict:
    """Prepare evaluation environment"""
    logger.info("Preparing evaluation environment")
    
    # Create directories
    directories = ["/data", "/results", "/visualizations", "/config"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Set environment variables
    evaluators = input_data.get("evaluators", ["skill_invocation", "performance", "cost"])
    os.environ["EVALUATORS"] = ",".join(evaluators)
    os.environ["QUALITY_GATE_SCORE"] = str(input_data.get("quality_gate_score", 0.8))
    os.environ["QUALITY_GATE_PASS_RATE"] = str(input_data.get("quality_gate_pass_rate", 0.85))
    
    return {"status": "success", "directories_created": directories}

@activity.defn
async def generate_sample_traces(input_data: dict) -> dict:
    """Generate sample traces for evaluation"""
    logger.info(f"Generating {input_data.get('trace_count', 100)} sample traces")
    
    try:
        from example_usage import generate_sample_traces
        
        trace_count = input_data.get("trace_count", 100)
        traces = generate_sample_traces(trace_count)
        
        # Save traces to file
        traces_file = "/data/sample_traces.json"
        import json
        with open(traces_file, 'w') as f:
            json.dump({"traces": traces}, f, indent=2)
        
        return {
            "status": "success",
            "trace_count": len(traces),
            "traces_file": traces_file
        }
    except Exception as e:
        logger.error(f"Failed to generate sample traces: {e}")
        raise

@activity.defn
async def run_evaluation_activity(input_data: dict) -> dict:
    """Run evaluation activity"""
    logger.info("Running evaluation activity")
    
    try:
        evaluators = input_data.get("evaluators", ["skill_invocation", "performance", "cost"])
        traces_file = "/data/sample_traces.json"
        
        # Load traces
        import json
        with open(traces_file, 'r') as f:
            data = json.load(f)
        traces = data["traces"]
        
        # Run evaluation
        result = evaluation_framework.evaluate_traces(traces, evaluators)
        
        # Save results
        results_file = "/results/evaluation_results.json"
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        return {
            "status": "success",
            "results_file": results_file,
            "summary": result.get("summary", {})
        }
    except Exception as e:
        logger.error(f"Evaluation activity failed: {e}")
        raise

@activity.defn
async def generate_visualizations(input_data: dict) -> dict:
    """Generate evaluation visualizations"""
    logger.info("Generating visualizations")
    
    try:
        traces_file = "/data/sample_traces.json"
        viz_dir = "/visualizations"
        
        # Load traces
        import json
        with open(traces_file, 'r') as f:
            data = json.load(f)
        traces = data["traces"]
        
        # Run evaluation for visualization data
        result = evaluation_framework.evaluate_traces(traces)
        
        # Generate visualizations
        visualizer.create_performance_dashboard(result, f"{viz_dir}/performance_dashboard.png")
        visualizer.create_trend_analysis(result, f"{viz_dir}/trend_analysis.png")
        visualizer.create_model_comparison(result, f"{viz_dir}/model_comparison.png")
        visualizer.generate_html_report(result, f"{viz_dir}/evaluation_report.html")
        
        return {
            "status": "success",
            "visualizations": {
                "performance_dashboard": f"{viz_dir}/performance_dashboard.png",
                "trend_analysis": f"{viz_dir}/trend_analysis.png",
                "model_comparison": f"{viz_dir}/model_comparison.png",
                "html_report": f"{viz_dir}/evaluation_report.html"
            }
        }
    except Exception as e:
        logger.error(f"Visualization generation failed: {e}")
        raise

@activity.defn
async def check_quality_gates(input_data: dict) -> dict:
    """Check quality gate compliance"""
    logger.info("Checking quality gates")
    
    try:
        # Load evaluation results
        import json
        with open("/results/evaluation_results.json", 'r') as f:
            results = json.load(f)
        
        summary = results.get("summary", {})
        overall_score = summary.get("overall_score", 0.0)
        pass_rate = summary.get("overall_pass_rate", 0.0)
        
        # Check quality gates
        score_threshold = input_data.get("quality_gate_score", 0.8)
        rate_threshold = input_data.get("quality_gate_pass_rate", 0.85)
        
        passed = (overall_score >= score_threshold) and (pass_rate >= rate_threshold)
        
        quality_gate_results = {
            "passed": passed,
            "overall_score": overall_score,
            "pass_rate": pass_rate,
            "score_threshold": score_threshold,
            "rate_threshold": rate_threshold,
            "checked_at": workflow.now().isoformat()
        }
        
        # Save quality gate results
        with open("/results/quality_gate_results.json", 'w') as f:
            json.dump(quality_gate_results, f, indent=2)
        
        return quality_gate_results
    except Exception as e:
        logger.error(f"Quality gate check failed: {e}")
        raise

@activity.defn
async def send_evaluation_notification(email: str, notification_data: dict) -> dict:
    """Send evaluation notification"""
    logger.info(f"Sending evaluation notification to {email}")
    
    try:
        # In a real implementation, this would send an email
        # For now, we'll just log and save the notification
        
        subject = "AI Agent Evaluation Results"
        if quality_gates := notification_data.get("quality_gates"):
            if quality_gates.get("passed"):
                subject = "✅ AI Agent Evaluation PASSED"
            else:
                subject = "❌ AI Agent Evaluation FAILED"
        
        notification = {
            "email": email,
            "subject": subject,
            "sent_at": workflow.now().isoformat(),
            "data": notification_data
        }
        
        # Save notification for audit
        import json
        with open("/results/notification.json", 'w') as f:
            json.dump(notification, f, indent=2)
        
        logger.info(f"Notification prepared: {subject}")
        return {"status": "success", "subject": subject}
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise

@workflow.defn
class EvaluationWorkflow:
    """Main evaluation workflow"""
    
    @workflow.run
    async def run(self, input_data: dict) -> dict:
        """Run evaluation workflow"""
        logger.info("Starting AI Agent Evaluation Workflow")
        
        try:
            # Step 1: Prepare environment
            await workflow.execute_activity(
                prepare_evaluation_environment,
                input_data,
                start_to_close_timeout=timedelta(minutes=5)
            )
            
            # Step 2: Generate sample traces
            await workflow.execute_activity(
                generate_sample_traces,
                input_data,
                start_to_close_timeout=timedelta(minutes=10)
            )
            
            # Step 3: Run evaluation
            evaluation_result = await workflow.execute_activity(
                run_evaluation_activity,
                input_data,
                start_to_close_timeout=timedelta(minutes=30)
            )
            
            # Step 4: Generate visualizations
            viz_result = await workflow.execute_activity(
                generate_visualizations,
                input_data,
                start_to_close_timeout=timedelta(minutes=15)
            )
            
            # Step 5: Check quality gates
            quality_gate_result = await workflow.execute_activity(
                check_quality_gates,
                input_data,
                start_to_close_timeout=timedelta(minutes=5)
            )
            
            # Step 6: Send notification if email provided
            if email := input_data.get("notification_email"):
                notification_data = {
                    "evaluation_results": evaluation_result,
                    "visualizations": viz_result,
                    "quality_gates": quality_gate_result
                }
                await workflow.execute_activity(
                    send_evaluation_notification,
                    email,
                    notification_data,
                    start_to_close_timeout=timedelta(minutes=5)
                )
            
            # Return results
            return {
                "workflow_id": workflow.info().workflow_id,
                "status": "completed",
                "evaluation_results": evaluation_result,
                "visualizations": viz_result,
                "quality_gates": quality_gate_result,
                "completed_at": workflow.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Evaluation workflow failed: {e}")
            raise

@workflow.defn
class ScheduledEvaluationWorkflow:
    """Scheduled evaluation workflow"""
    
    @workflow.run
    async def run(self) -> dict:
        """Run scheduled evaluation"""
        logger.info("Starting scheduled evaluation workflow")
        
        input_data = {
            "evaluators": ["skill_invocation", "performance", "cost", "monitoring", "health_check", "security", "compliance"],
            "trace_count": 100,
            "quality_gate_score": 0.8,
            "quality_gate_pass_rate": 0.85,
            "notification_email": "dev-team@company.com"
        }
        
        # Run main evaluation workflow
        return await workflow.execute_child_workflow(
            EvaluationWorkflow.run,
            input_data,
            id=f"scheduled-evaluation-{int(workflow.now().timestamp())}",
            execution_timeout=timedelta(hours=1)
        )

@workflow.defn
class EventDrivenEvaluationWorkflow:
    """Event-driven evaluation workflow"""
    
    @workflow.run
    async def run(self, trigger_data: dict) -> dict:
        """Run event-driven evaluation"""
        logger.info(f"Event-driven evaluation triggered: {trigger_data}")
        
        # Determine evaluators based on trigger
        base_evaluators = ["skill_invocation", "performance", "cost", "monitoring", "health_check"]
        urgency = trigger_data.get("urgency", "normal")
        
        if urgency in ["high", "critical"]:
            base_evaluators.extend(["security", "compliance"])
        
        input_data = {
            "evaluators": base_evaluators,
            "trace_count": 50,
            "quality_gate_score": 0.8,
            "quality_gate_pass_rate": 0.85,
            "trigger_data": trigger_data
        }
        
        # Run main evaluation workflow
        return await workflow.execute_child_workflow(
            EvaluationWorkflow.run,
            input_data,
            id=f"event-evaluation-{int(workflow.now().timestamp())}",
            execution_timeout=timedelta(hours=1)
        )

async def main():
    """Main function to run the worker"""
    logger.info("Starting AI Agent Evaluation Temporal Worker")
    
    # Connect to Temporal server
    client = await Client.connect("localhost:7233")
    
    # Create worker with activities and workflows
    activities = [
        prepare_evaluation_environment,
        generate_sample_traces,
        run_evaluation_activity,
        generate_visualizations,
        check_quality_gates,
        send_evaluation_notification,
    ]
    
    workflows = [
        EvaluationWorkflow,
        ScheduledEvaluationWorkflow,
        EventDrivenEvaluationWorkflow,
    ]
    
    # Run worker
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=workflows,
        activities=activities
    )
    
    logger.info(f"Worker started for task queue: {TASK_QUEUE}")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
