import json
from flask import Flask, render_template_string, jsonify
from pathlib import Path

app = Flask(__name__)

RESULTS_DIR = Path("../evaluation-results")  # Relative to dashboard directory

@app.route('/')
def dashboard():
    """Main dashboard page"""
    latest_file = RESULTS_DIR / "latest.json"

    if not latest_file.exists():
        return """
        <html>
        <head><title>GitOps Agent Evaluation Dashboard</title></head>
        <body>
        <h1>GitOps Agent Evaluation Dashboard</h1>
        <p>No evaluation data available. Run the evaluation pipeline first.</p>
        </body>
        </html>
        """

    with open(latest_file, 'r') as f:
        data = json.load(f)

    # Create dashboard HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>GitOps Agent Evaluation Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .metric {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
            .metric h3 {{ margin-top: 0; color: #333; }}
            .pass {{ color: #28a745; font-weight: bold; }}
            .fail {{ color: #dc3545; font-weight: bold; }}
            .warning {{ color: #ffc107; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f8f9fa; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>GitOps Agent Evaluation Dashboard</h1>
            <p>Last updated: {data.get('summary', {}).get('evaluation_timestamp', 'Unknown')}</p>

            <div class="metric">
                <h3>📊 Summary</h3>
                <p><strong>Total Traces:</strong> {data.get('summary', {}).get('total_traces', 0)}</p>
                <p><strong>Total Evaluations:</strong> {data.get('summary', {}).get('total_evaluations', 0)}</p>
                <p><strong>Average Score:</strong> {data.get('summary', {}).get('average_score', 0):.3f}</p>
                <p><strong>Pass Rate:</strong> <span class="{'pass' if data.get('summary', {}).get('pass_rate', 0) >= 0.8 else 'fail' if data.get('summary', {}).get('pass_rate', 0) < 0.7 else 'warning'}">{data.get('summary', {}).get('pass_rate', 0):.1%}</span></p>
                <p><strong>Time Range:</strong> {data.get('summary', {}).get('time_range', 'N/A')}</p>
            </div>

            <div class="metric">
                <h3>🔍 Evaluator Performance</h3>
                <table>
                    <tr>
                        <th>Evaluator</th>
                        <th>Count</th>
                        <th>Average Score</th>
                        <th>Pass Rate</th>
                        <th>Min Score</th>
                        <th>Max Score</th>
                    </tr>
    """

    for evaluator, stats in data.get('by_evaluator', {}).items():
        html += f"""
                    <tr>
                        <td>{evaluator}</td>
                        <td>{stats.get('count', 0)}</td>
                        <td>{stats.get('average_score', 0):.3f}</td>
                        <td><span class="{'pass' if stats.get('pass_rate', 0) >= 0.8 else 'fail'}">{stats.get('pass_rate', 0):.1%}</span></td>
                        <td>{stats.get('min_score', 0):.3f}</td>
                        <td>{stats.get('max_score', 0):.3f}</td>
                    </tr>
        """

    failing_traces = data.get('failing_traces', [])
    html += f"""
                </table>
            </div>

            <div class="metric">
                <h3>❌ Failing Traces ({len(failing_traces)})</h3>
    """

    if failing_traces:
        html += """
                <table>
                    <tr>
                        <th>Trace ID</th>
                        <th>Evaluator</th>
                        <th>Score</th>
                        <th>Details</th>
                    </tr>
        """
        for trace in failing_traces[:10]:  # Show first 10
            details = trace.get('details', {})
            details_str = ", ".join([f"{k}: {v}" for k, v in details.items() if k != 'details'])
            html += f"""
                    <tr>
                        <td>{trace.get('trace_id', 'N/A')}</td>
                        <td>{trace.get('evaluator', 'N/A')}</td>
                        <td>{trace.get('score', 0):.3f}</td>
                        <td>{details_str}</td>
                    </tr>
            """
        html += "</table>"
    else:
        html += "<p>No failing traces - all evaluations passed! ✅</p>"

    trends = data.get('trends', {})
    html += f"""
            </div>

            <div class="metric">
                <h3>📈 Trends</h3>
                <ul>
    """

    for trend_key, trend_value in trends.items():
        if trend_key == 'score_trend':
            html += f"<li>Score Trend: {trend_value}</li>"
        elif trend_key == 'pass_rate_trend':
            html += f"<li>Pass Rate Trend: {trend_value}</li>"
        elif trend_key == 'recommendations':
            html += "<li><strong>Recommendations:</strong><ul>"
            for rec in trend_value:
                html += f"<li>{rec}</li>"
            html += "</ul></li>"

    html += """
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

    return html

@app.route('/api/latest')
def api_latest():
    """API endpoint for latest results"""
    latest_file = RESULTS_DIR / "latest.json"

    if not latest_file.exists():
        return jsonify({"error": "No evaluation data available"})

    with open(latest_file, 'r') as f:
        data = json.load(f)

    return jsonify(data)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": json.dumps(datetime.now().isoformat())})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
