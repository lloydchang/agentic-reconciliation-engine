#!/usr/bin/env python3
"""
GitOps Evaluation Alert System

Monitors evaluation results and sends alerts for failures and regressions.
"""

import json
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Any, List, Optional

class GitOpsEvaluationAlerter:
    """Alert system for GitOps agent evaluation failures and regressions"""

    def __init__(self, results_dir: str = "evaluation-results"):
        """
        Initialize the alerter

        Args:
            results_dir: Directory containing evaluation results
        """
        self.results_dir = Path(results_dir)

        # Alert thresholds
        self.thresholds = {
            "min_pass_rate": 0.8,  # 80% pass rate
            "min_average_score": 0.7,  # 0.7 average score
            "max_regression_threshold": 0.1,  # 10% regression threshold
            "max_failing_traces": 5  # Maximum number of failing traces
        }

        # Email configuration (from environment)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.alert_recipients = os.getenv("ALERT_RECIPIENTS", "").split(",")

        # Alert state tracking
        self.alert_state_file = self.results_dir / "alert_state.json"
        self._load_alert_state()

    def _load_alert_state(self):
        """Load previous alert state"""
        self.alert_state = {
            "last_alert_time": None,
            "last_pass_rate": None,
            "last_average_score": None,
            "consecutive_failures": 0
        }

        if self.alert_state_file.exists():
            try:
                with open(self.alert_state_file, "r") as f:
                    self.alert_state.update(json.load(f))
            except Exception as e:
                print(f"Warning: Could not load alert state: {e}")

    def _save_alert_state(self):
        """Save current alert state"""
        try:
            with open(self.alert_state_file, "w") as f:
                json.dump(self.alert_state, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save alert state: {e}")

    def check_and_alert(self, latest_results: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check evaluation results and send alerts if needed

        Args:
            latest_results: Latest evaluation results (loads from file if not provided)

        Returns:
            True if alert was sent, False otherwise
        """
        if latest_results is None:
            latest_results = self._get_latest_results()

        if "error" in latest_results:
            print(f"No results to check: {latest_results['error']}")
            return False

        # Check for alert conditions
        alert_reasons = self._check_alert_conditions(latest_results)

        if not alert_reasons:
            # Reset consecutive failures on success
            self.alert_state["consecutive_failures"] = 0
            self._save_alert_state()
            return False

        # Check if we should send alert (avoid spam)
        if not self._should_send_alert():
            return False

        # Send alert
        success = self._send_alert(latest_results, alert_reasons)

        if success:
            # Update alert state
            self.alert_state["last_alert_time"] = datetime.now().isoformat()
            self.alert_state["consecutive_failures"] += 1
            self._save_alert_state()

        return success

    def _get_latest_results(self) -> Dict[str, Any]:
        """Get the latest evaluation results"""
        latest_file = self.results_dir / "latest.json"
        if latest_file.exists():
            try:
                with open(latest_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                return {"error": f"Failed to load results: {e}"}
        return {"error": "No evaluation results available"}

    def _check_alert_conditions(self, results: Dict[str, Any]) -> List[str]:
        """
        Check if evaluation results trigger alert conditions

        Args:
            results: Evaluation results

        Returns:
            List of alert reasons (empty if no alerts needed)
        """
        alert_reasons = []
        summary = results.get("summary", {})

        # Check pass rate
        pass_rate = summary.get("pass_rate", 1.0)
        if pass_rate < self.thresholds["min_pass_rate"]:
            alert_reasons.append(
                f"Pass rate too low: {pass_rate:.1%} (threshold: {self.thresholds['min_pass_rate']:.1%})"
            )

        # Check average score
        average_score = summary.get("average_score", 1.0)
        if average_score < self.thresholds["min_average_score"]:
            alert_reasons.append(
                f"Average score too low: {average_score:.2f} (threshold: {self.thresholds['min_average_score']:.2f})"
            )

        # Check for regression
        last_pass_rate = self.alert_state.get("last_pass_rate")
        if last_pass_rate is not None:
            regression = last_pass_rate - pass_rate
            if regression > self.thresholds["max_regression_threshold"]:
                alert_reasons.append(
                    f"Performance regression: {regression:.1%} drop from {last_pass_rate:.1%} to {pass_rate:.1%}"
                )

        # Check failing traces count
        failing_traces = results.get("failing_traces", [])
        if len(failing_traces) > self.thresholds["max_failing_traces"]:
            alert_reasons.append(
                f"Too many failing traces: {len(failing_traces)} (threshold: {self.thresholds['max_failing_traces']})"
            )

        # Update state for next check
        self.alert_state["last_pass_rate"] = pass_rate
        self.alert_state["last_average_score"] = average_score

        return alert_reasons

    def _should_send_alert(self) -> bool:
        """
        Determine if an alert should be sent (avoid spam)

        Returns:
            True if alert should be sent
        """
        last_alert_time = self.alert_state.get("last_alert_time")
        if last_alert_time is None:
            return True

        # Parse last alert time
        try:
            last_alert = datetime.fromisoformat(last_alert_time)
            time_since_last_alert = datetime.now() - last_alert

            # Don't send alerts more than once per hour for consecutive failures
            consecutive_failures = self.alert_state.get("consecutive_failures", 0)

            if consecutive_failures == 0:
                return True  # Always alert on first failure
            elif consecutive_failures == 1 and time_since_last_alert > timedelta(minutes=30):
                return True  # Alert again after 30 minutes
            elif time_since_last_alert > timedelta(hours=1):
                return True  # Alert again after 1 hour for ongoing issues

            return False

        except Exception as e:
            print(f"Warning: Could not parse last alert time: {e}")
            return True  # Send alert if we can't determine timing

    def _send_alert(self, results: Dict[str, Any], reasons: List[str]) -> bool:
        """
        Send alert notification

        Args:
            results: Evaluation results
            reasons: List of alert reasons

        Returns:
            True if alert sent successfully
        """
        if not self.alert_recipients or not self.alert_recipients[0]:
            print("No alert recipients configured, logging alert instead")
            self._log_alert(results, reasons)
            return True

        try:
            # Create message
            subject = "GitOps Agent Evaluation Alert"
            body = self._create_alert_message(results, reasons)

            # Send email
            return self._send_email(subject, body)

        except Exception as e:
            print(f"Failed to send alert: {e}")
            self._log_alert(results, reasons)
            return False

    def _create_alert_message(self, results: Dict[str, Any], reasons: List[str]) -> str:
        """Create alert message content"""
        summary = results.get("summary", {})

        message = f"""
GitOps Agent Evaluation Alert
{'='*40}

Alert triggered at: {datetime.now().isoformat()}

SUMMARY:
- Total traces: {summary.get('total_traces', 0)}
- Average score: {summary.get('average_score', 0):.2f}
- Pass rate: {summary.get('pass_rate', 0):.1%}
- Time range: {summary.get('time_range', 'Unknown')}

ALERT REASONS:
{chr(10).join(f'- {reason}' for reason in reasons)}

EVALUATOR PERFORMANCE:
"""

        evaluator_stats = results.get("by_evaluator", {})
        for evaluator, stats in evaluator_stats.items():
            message += f"""
{evaluator}:
  - Evaluations: {stats.get('count', 0)}
  - Average score: {stats.get('average_score', 0):.2f}
  - Pass rate: {stats.get('pass_rate', 0):.1%}
"""

        failing_traces = results.get("failing_traces", [])
        if failing_traces:
            message += f"""

FAILING TRACES ({len(failing_traces)}):
"""
            for i, trace in enumerate(failing_traces[:5]):  # Show first 5
                message += f"""
  {i+1}. Trace ID: {trace.get('trace_id', 'Unknown')}
     Evaluator: {trace.get('evaluator', 'Unknown')}
     Score: {trace.get('score', 0):.2f}
"""

        message += """

Please investigate the failing evaluations and address any performance regressions.
"""

        return message

    def _send_email(self, subject: str, body: str) -> bool:
        """Send alert via email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = ", ".join(self.alert_recipients)
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.smtp_username, self.alert_recipients, text)
            server.quit()

            print(f"Alert email sent to {len(self.alert_recipients)} recipients")
            return True

        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def _log_alert(self, results: Dict[str, Any], reasons: List[str]):
        """Log alert to file when email is not available"""
        alert_log = {
            "timestamp": datetime.now().isoformat(),
            "reasons": reasons,
            "summary": results.get("summary", {}),
            "failing_traces_count": len(results.get("failing_traces", []))
        }

        alert_log_file = self.results_dir / "alerts.log"
        try:
            with open(alert_log_file, "a") as f:
                json.dump(alert_log, f, default=str)
                f.write("\n")
            print(f"Alert logged to {alert_log_file}")
        except Exception as e:
            print(f"Failed to log alert: {e}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="GitOps Evaluation Alert System")
    parser.add_argument("--results-dir", default="evaluation-results", help="Results directory")
    parser.add_argument("--check-only", action="store_true", help="Check conditions without sending alerts")

    args = parser.parse_args()

    # Create alerter
    alerter = GitOpsEvaluationAlerter(results_dir=args.results_dir)

    # Check and alert
    alert_sent = alerter.check_and_alert()

    if args.check_only:
        print(f"Alert check complete. Alert sent: {alert_sent}")
    elif alert_sent:
        print("Alert sent successfully")
    else:
        print("No alert needed")


if __name__ == "__main__":
    main()
