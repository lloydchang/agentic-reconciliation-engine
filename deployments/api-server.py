#!/usr/bin/env python3
"""
Flask API Server for AI Agent Evaluation Framework

Provides REST API endpoints for running evaluations,
checking status, and retrieving results.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import threading
import uuid

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add framework to path
import sys
sys.path.append(str(Path(__file__).parent))

from main import TracingEvaluationFramework
from visualization import EvaluationVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables
evaluation_framework = TracingEvaluationFramework()
visualizer = EvaluationVisualizer()
running_evaluations: Dict[str, Dict[str, Any]] = {}
evaluation_results: Dict[str, Dict[str, Any]] = {}

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = '/data'
app.config['RESULTS_FOLDER'] = '/results'
app.config['VISUALIZATION_FOLDER'] = '/visualizations'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
os.makedirs(app.config['VISUALIZATION_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'json', 'txt'}

def run_evaluation_async(evaluation_id: str, traces: List[Dict[str, Any]], 
                         evaluators: List[str], options: Dict[str, Any]):
    """Run evaluation asynchronously"""
    try:
        # Update status
        running_evaluations[evaluation_id]['status'] = 'running'
        running_evaluations[evaluation_id]['started_at'] = datetime.utcnow().isoformat()
        
        # Run evaluation
        result = evaluation_framework.evaluate_traces(traces, evaluators)
        
        # Generate visualizations if requested
        visualizations = {}
        if options.get('generate_visualizations', True):
            try:
                viz_dir = os.path.join(app.config['VISUALIZATION_FOLDER'], evaluation_id)
                os.makedirs(viz_dir, exist_ok=True)
                
                visualizer.create_performance_dashboard(
                    result, 
                    os.path.join(viz_dir, 'performance_dashboard.png')
                )
                visualizer.create_trend_analysis(
                    result,
                    os.path.join(viz_dir, 'trend_analysis.png')
                )
                visualizer.create_model_comparison(
                    result,
                    os.path.join(viz_dir, 'model_comparison.png')
                )
                visualizer.generate_html_report(
                    result,
                    os.path.join(viz_dir, 'evaluation_report.html')
                )
                
                visualizations = {
                    'performance_dashboard': f'/visualizations/{evaluation_id}/performance_dashboard.png',
                    'trend_analysis': f'/visualizations/{evaluation_id}/trend_analysis.png',
                    'model_comparison': f'/visualizations/{evaluation_id}/model_comparison.png',
                    'html_report': f'/visualizations/{evaluation_id}/evaluation_report.html'
                }
            except Exception as e:
                logger.error(f"Visualization generation failed: {e}")
        
        # Store results
        evaluation_results[evaluation_id] = {
            'id': evaluation_id,
            'status': 'completed',
            'completed_at': datetime.utcnow().isoformat(),
            'result': result,
            'visualizations': visualizations,
            'options': options
        }
        
        # Update running evaluation status
        running_evaluations[evaluation_id]['status'] = 'completed'
        running_evaluations[evaluation_id]['completed_at'] = datetime.utcnow().isoformat()
        
        # Save results to file
        results_file = os.path.join(app.config['RESULTS_FOLDER'], f'{evaluation_id}.json')
        with open(results_file, 'w') as f:
            json.dump(evaluation_results[evaluation_id], f, indent=2, default=str)
        
        logger.info(f"Evaluation {evaluation_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Evaluation {evaluation_id} failed: {e}")
        running_evaluations[evaluation_id]['status'] = 'failed'
        running_evaluations[evaluation_id]['error'] = str(e)
        running_evaluations[evaluation_id]['failed_at'] = datetime.utcnow().isoformat()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'evaluators': list(evaluation_framework.evaluators.keys())
    })

@app.route('/evaluators', methods=['GET'])
def list_evaluators():
    """List available evaluators"""
    evaluators_info = {}
    for name, evaluator in evaluation_framework.evaluators.items():
        evaluators_info[name] = {
            'name': name,
            'class': evaluator.__class__.__name__,
            'description': getattr(evaluator, '__doc__', 'No description available')
        }
    
    return jsonify({
        'evaluators': evaluators_info,
        'total_count': len(evaluators_info)
    })

@app.route('/evaluate', methods=['POST'])
def start_evaluation():
    """Start a new evaluation"""
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data or 'traces' not in data:
            return jsonify({'error': 'Missing traces data'}), 400
        
        traces = data['traces']
        evaluators = data.get('evaluators', list(evaluation_framework.evaluators.keys()))
        options = data.get('options', {})
        
        # Validate evaluators
        invalid_evaluators = [e for e in evaluators if e not in evaluation_framework.evaluators]
        if invalid_evaluators:
            return jsonify({
                'error': f'Invalid evaluators: {invalid_evaluators}',
                'available_evaluators': list(evaluation_framework.evaluators.keys())
            }), 400
        
        # Generate evaluation ID
        evaluation_id = str(uuid.uuid4())
        
        # Store evaluation info
        running_evaluations[evaluation_id] = {
            'id': evaluation_id,
            'status': 'queued',
            'created_at': datetime.utcnow().isoformat(),
            'traces_count': len(traces),
            'evaluators': evaluators,
            'options': options
        }
        
        # Start evaluation in background thread
        thread = threading.Thread(
            target=run_evaluation_async,
            args=(evaluation_id, traces, evaluators, options)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'evaluation_id': evaluation_id,
            'status': 'queued',
            'message': 'Evaluation started',
            'traces_count': len(traces),
            'evaluators': evaluators
        })
        
    except Exception as e:
        logger.error(f"Failed to start evaluation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/evaluate/upload', methods=['POST'])
def upload_and_evaluate():
    """Upload traces file and start evaluation"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only JSON files are allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Load traces from file
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        traces = data.get('traces', [])
        if not traces:
            return jsonify({'error': 'No traces found in file'}), 400
        
        # Get evaluators and options from form
        evaluators = request.form.get('evaluators', ','.join(evaluation_framework.evaluators.keys()))
        evaluators = evaluators.split(',') if evaluators else list(evaluation_framework.evaluators.keys())
        
        options = {}
        if 'generate_visualizations' in request.form:
            options['generate_visualizations'] = request.form['generate_visualizations'].lower() == 'true'
        
        # Generate evaluation ID
        evaluation_id = str(uuid.uuid4())
        
        # Store evaluation info
        running_evaluations[evaluation_id] = {
            'id': evaluation_id,
            'status': 'queued',
            'created_at': datetime.utcnow().isoformat(),
            'source_file': filename,
            'traces_count': len(traces),
            'evaluators': evaluators,
            'options': options
        }
        
        # Start evaluation in background thread
        thread = threading.Thread(
            target=run_evaluation_async,
            args=(evaluation_id, traces, evaluators, options)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'evaluation_id': evaluation_id,
            'status': 'queued',
            'message': 'Evaluation started from uploaded file',
            'source_file': filename,
            'traces_count': len(traces),
            'evaluators': evaluators
        })
        
    except Exception as e:
        logger.error(f"Failed to process uploaded file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/evaluate/<evaluation_id>/status', methods=['GET'])
def get_evaluation_status(evaluation_id):
    """Get evaluation status"""
    if evaluation_id in running_evaluations:
        return jsonify(running_evaluations[evaluation_id])
    elif evaluation_id in evaluation_results:
        return jsonify(evaluation_results[evaluation_id])
    else:
        return jsonify({'error': 'Evaluation not found'}), 404

@app.route('/evaluate/<evaluation_id>/results', methods=['GET'])
def get_evaluation_results(evaluation_id):
    """Get evaluation results"""
    if evaluation_id not in evaluation_results:
        return jsonify({'error': 'Evaluation results not found'}), 404
    
    result = evaluation_results[evaluation_id].copy()
    
    # Remove large binary data from response
    if 'result' in result:
        result_data = result['result']
        if 'individual_results' in result_data:
            # Limit individual results for performance
            result_data['individual_results'] = result_data['individual_results'][:10]
    
    return jsonify(result)

@app.route('/evaluate/<evaluation_id>/visualizations/<filename>', methods=['GET'])
def get_visualization(evaluation_id, filename):
    """Get visualization file"""
    filepath = os.path.join(app.config['VISUALIZATION_FOLDER'], evaluation_id, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Visualization file not found'}), 404
    
    return send_file(filepath, as_attachment=False)

@app.route('/evaluations', methods=['GET'])
def list_evaluations():
    """List all evaluations"""
    limit = request.args.get('limit', 50, type=int)
    status_filter = request.args.get('status', '')
    
    all_evaluations = {}
    
    # Add running evaluations
    for eval_id, eval_data in running_evaluations.items():
        if not status_filter or eval_data['status'] == status_filter:
            all_evaluations[eval_id] = eval_data
    
    # Add completed evaluations
    for eval_id, eval_data in evaluation_results.items():
        if not status_filter or eval_data['status'] == status_filter:
            all_evaluations[eval_id] = eval_data
    
    # Sort by creation time (newest first)
    sorted_evaluations = sorted(
        all_evaluations.items(),
        key=lambda x: x[1].get('created_at', ''),
        reverse=True
    )
    
    # Apply limit
    if limit > 0:
        sorted_evaluations = sorted_evaluations[:limit]
    
    return jsonify({
        'evaluations': dict(sorted_evaluations),
        'total_count': len(all_evaluations),
        'filtered_count': len(sorted_evaluations)
    })

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get system metrics"""
    total_evaluations = len(running_evaluations) + len(evaluation_results)
    running_count = sum(1 for e in running_evaluations.values() if e['status'] == 'running')
    completed_count = sum(1 for e in evaluation_results.values() if e['status'] == 'completed')
    failed_count = sum(1 for e in running_evaluations.values() if e['status'] == 'failed')
    
    # Calculate average scores
    scores = []
    for result in evaluation_results.values():
        if result['status'] == 'completed' and 'result' in result:
            summary = result['result'].get('summary', {})
            if 'overall_score' in summary:
                scores.append(summary['overall_score'])
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return jsonify({
        'total_evaluations': total_evaluations,
        'running_evaluations': running_count,
        'completed_evaluations': completed_count,
        'failed_evaluations': failed_count,
        'average_score': avg_score,
        'evaluators_available': len(evaluation_framework.evaluators),
        'system_uptime': datetime.utcnow().isoformat()
    })

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting AI Agent Evaluation API Server")
    app.run(host='0.0.0.0', port=5000, debug=False)
