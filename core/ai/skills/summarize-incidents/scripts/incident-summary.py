#!/usr/bin/env python3
"""
Advanced AI Incident Summarization Script

This script processes monitoring alerts and generates AI-enhanced structured summaries
for incident response and documentation, including NLP summarization, ML root cause analysis,
and predictive insights.
"""

import json
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter
import re

# AI/ML imports
try:
    import numpy as np
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    from transformers import pipeline
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    import nltk
    # Download required NLTK data
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except ImportError as e:
    logging.warning(f"AI/ML libraries not available: {e}. Falling back to basic functionality.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AdvancedIncidentSummarizer:
    def __init__(self):
        self.severity_levels = {
            'critical': 4,
            'warning': 3,
            'info': 2,
            'debug': 1
        }
        
        # Initialize AI models if available
        self.nlp_summarizer = None
        self.tfidf_vectorizer = None
        try:
            self.nlp_summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
            self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        except Exception as e:
            logging.warning(f"Could not initialize AI models: {e}")
    
    def parse_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure alert data"""
        return {
            'timestamp': alert_data.get('timestamp', datetime.utcnow().isoformat()),
            'severity': alert_data.get('severity', 'info'),
            'service': alert_data.get('service', 'unknown'),
            'message': alert_data.get('message', ''),
            'labels': alert_data.get('labels', {}),
            'annotations': alert_data.get('annotations', {})
        }
    
    def generate_summary(self, alerts: List[Dict[str, Any]], include_historical: bool = False) -> Dict[str, Any]:
        """Generate AI-enhanced incident summary from multiple alerts"""
        if not alerts:
            return {'error': 'No alerts provided'}
        
        # Sort alerts by severity and timestamp
        sorted_alerts = sorted(alerts, key=lambda x: (
            self.severity_levels.get(x.get('severity', 'info'), 0),
            x.get('timestamp', '')
        ), reverse=True)
        
        # Extract key information
        affected_services = list(set(alert.get('service', 'unknown') for alert in sorted_alerts))
        max_severity = max(self.severity_levels.get(alert.get('severity', 'info'), 0) for alert in sorted_alerts)
        
        # Generate timeline
        timeline = []
        for alert in sorted_alerts[:10]:  # Limit to first 10 alerts
            timeline.append({
                'time': alert.get('timestamp', ''),
                'event': f"{alert.get('service', 'unknown')}: {alert.get('message', '')[:100]}...",
                'severity': alert.get('severity', 'info')
            })
        
        # AI-powered root cause analysis
        potential_causes = self._ml_root_cause_analysis(sorted_alerts)
        
        # NLP-based summary generation
        nlp_summary = self._nlp_summarize_incident(sorted_alerts)
        
        # Predictive insights
        predictive_insights = self._predictive_analysis(sorted_alerts) if include_historical else []
        
        # Generate recommendations
        recommendations = self._generate_recommendations(sorted_alerts, potential_causes)
        
        return {
            'incident_id': f"inc-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            'summary': {
                'title': f"{'Critical' if max_severity == 4 else 'Warning' if max_severity == 3 else 'Info'}: {', '.join(affected_services)}",
                'severity': max_severity,
                'affected_services': affected_services,
                'alert_count': len(alerts),
                'first_alert': sorted_alerts[-1].get('timestamp', ''),
                'latest_alert': sorted_alerts[0].get('timestamp', ''),
                'nlp_summary': nlp_summary
            },
            'timeline': timeline,
            'potential_causes': potential_causes,
            'predictive_insights': predictive_insights,
            'recommendations': recommendations,
            'generated_at': datetime.utcnow().isoformat(),
            'ai_enhanced': bool(self.nlp_summarizer and self.tfidf_vectorizer)
        }
    
    def _ml_root_cause_analysis(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use ML clustering to identify root causes"""
        if not self.tfidf_vectorizer or not alerts:
            return self._basic_root_cause_analysis(alerts)
        
        try:
            # Extract messages for clustering
            messages = [alert.get('message', '') for alert in alerts]
            
            # Vectorize messages
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(messages)
            
            # Perform clustering (dynamic number of clusters based on data)
            n_clusters = min(len(alerts), max(2, len(alerts) // 3))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(tfidf_matrix)
            
            # Analyze clusters to identify root causes
            cluster_causes = []
            for cluster_id in range(n_clusters):
                cluster_messages = [msg for msg, clust in zip(messages, clusters) if clust == cluster_id]
                if cluster_messages:
                    # Find common patterns in cluster
                    common_words = self._extract_common_patterns(cluster_messages)
                    if common_words:
                        cluster_causes.append({
                            'cluster_id': cluster_id,
                            'size': len(cluster_messages),
                            'common_patterns': common_words,
                            'root_cause': self._infer_root_cause(common_words),
                            'confidence': len(cluster_messages) / len(alerts)
                        })
            
            # Sort by confidence and return top causes
            cluster_causes.sort(key=lambda x: x['confidence'], reverse=True)
            return cluster_causes[:5]
            
        except Exception as e:
            logging.warning(f"ML root cause analysis failed: {e}. Using basic analysis.")
            return self._basic_root_cause_analysis(alerts)
    
    def _basic_root_cause_analysis(self, alerts: List[Dict[str, Any]]) -> List[str]:
        """Fallback basic root cause analysis"""
        causes = []
        
        # Common patterns
        error_patterns = {
            'CrashLoopBackOff': 'Pod restart loops detected',
            'ImagePullBackOff': 'Container image pull failures',
            'MemoryPressure': 'Insufficient memory resources',
            'DiskPressure': 'Insufficient disk space',
            'NetworkUnavailable': 'Network connectivity issues',
            'OOMKilled': 'Out of memory errors',
            'ProbeFailure': 'Health check failures'
        }
        
        for alert in alerts:
            message = alert.get('message', '')
            for pattern, cause in error_patterns.items():
                if pattern in message:
                    if cause not in causes:
                        causes.append(cause)
        
        return causes[:5]
    
    def _extract_common_patterns(self, messages: List[str]) -> List[str]:
        """Extract common keywords/patterns from messages"""
        try:
            # Tokenize and remove stop words
            stop_words = set(stopwords.words('english'))
            all_words = []
            
            for msg in messages:
                tokens = word_tokenize(msg.lower())
                filtered_tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
                all_words.extend(filtered_tokens)
            
            # Count word frequencies
            word_counts = Counter(all_words)
            
            # Return most common words (excluding very common ones)
            common_words = [word for word, count in word_counts.most_common(10) if count > 1]
            return common_words
            
        except Exception as e:
            logging.warning(f"Pattern extraction failed: {e}")
            return []
    
    def _infer_root_cause(self, patterns: List[str]) -> str:
        """Infer root cause from common patterns"""
        pattern_text = ' '.join(patterns).lower()
        
        if 'memory' in pattern_text or 'oom' in pattern_text:
            return 'Memory resource exhaustion'
        elif 'disk' in pattern_text or 'storage' in pattern_text:
            return 'Storage resource issues'
        elif 'network' in pattern_text or 'connect' in pattern_text:
            return 'Network connectivity problems'
        elif 'crash' in pattern_text or 'restart' in pattern_text:
            return 'Application crashes or restarts'
        elif 'image' in pattern_text or 'pull' in pattern_text:
            return 'Container image issues'
        else:
            return ' '.join(patterns[:3])  # Fallback to top patterns
    
    def _nlp_summarize_incident(self, alerts: List[Dict[str, Any]]) -> str:
        """Generate NLP-based summary of the incident"""
        if not self.nlp_summarizer or not alerts:
            return self._basic_summarize_incident(alerts)
        
        try:
            # Combine all alert messages into a single text
            combined_text = ' '.join([alert.get('message', '') for alert in alerts])
            
            # Limit text length for summarization model
            if len(combined_text) > 1000:
                combined_text = combined_text[:1000] + '...'
            
            # Generate summary
            summary_result = self.nlp_summarizer(combined_text, max_length=100, min_length=30, do_sample=False)
            return summary_result[0]['summary_text']
            
        except Exception as e:
            logging.warning(f"NLP summarization failed: {e}. Using basic summary.")
            return self._basic_summarize_incident(alerts)
    
    def _basic_summarize_incident(self, alerts: List[Dict[str, Any]]) -> str:
        """Fallback basic incident summary"""
        services = list(set(alert.get('service', 'unknown') for alert in alerts))
        severities = [alert.get('severity', 'info') for alert in alerts]
        max_severity = max(self.severity_levels.get(sev, 0) for sev in severities)
        
        return f"Incident involving {len(services)} services with maximum severity '{max_severity}'. {len(alerts)} alerts generated."
    
    def _predictive_analysis(self, alerts: List[Dict[str, Any]]) -> List[str]:
        """Generate predictive insights based on alert patterns"""
        insights = []
        
        # Analyze patterns for prediction
        service_counts = Counter(alert.get('service', 'unknown') for alert in alerts)
        severity_counts = Counter(alert.get('severity', 'info') for alert in alerts)
        
        # High-frequency service alerts
        if service_counts:
            top_service = service_counts.most_common(1)[0][0]
            if service_counts[top_service] > len(alerts) * 0.5:
                insights.append(f"High alert frequency from {top_service} suggests potential systemic issues")
        
        # Escalating severity
        if severity_counts.get('critical', 0) > severity_counts.get('warning', 0):
            insights.append("Critical alerts dominate - consider immediate capacity scaling")
        
        # Time-based patterns (basic)
        timestamps = [datetime.fromisoformat(alert.get('timestamp', datetime.utcnow().isoformat())) for alert in alerts]
        if timestamps:
            time_span = max(timestamps) - min(timestamps)
            if time_span < timedelta(hours=1):
                insights.append("Rapid alert clustering suggests acute incident rather than gradual degradation")
        
        return insights[:3]  # Limit to top 3 insights
    
    def _generate_recommendations(self, alerts: List[Dict[str, Any]], causes: List[Any]) -> List[str]:
        """Generate actionable recommendations based on alerts and causes"""
        recommendations = []
        
        # Process causes for recommendations
        cause_texts = [cause.get('root_cause', cause) if isinstance(cause, dict) else cause for cause in causes]
        
        for cause in cause_texts:
            cause_lower = cause.lower()
            if 'memory' in cause_lower:
                recommendations.append("Scale up memory resources or optimize application memory usage")
            elif 'disk' in cause_lower or 'storage' in cause_lower:
                recommendations.append("Check disk space and implement log rotation/cleanup policies")
            elif 'network' in cause_lower:
                recommendations.append("Review network policies and connectivity between services")
            elif 'crash' in cause_lower or 'restart' in cause_lower:
                recommendations.append("Investigate application logs and implement proper error handling")
            elif 'image' in cause_lower:
                recommendations.append("Verify container image availability and registry access")
        
        # Add general recommendations if none specific
        if not recommendations:
            recommendations = [
                "Review recent deployments for potential causes",
                "Check cluster resource utilization",
                "Verify service dependencies and health",
                "Implement circuit breakers for resilient service communication"
            ]
        
        return recommendations[:5]

def main():
    """Main function to process alerts from stdin or file"""
    if len(sys.argv) < 2:
        print("Usage: python3 incident-summary.py <alert_file.json> [--historical]")
        print("Or pipe JSON alerts to stdin")
        sys.exit(1)
    
    try:
        # Parse arguments
        include_historical = '--historical' in sys.argv
        
        # Read alerts from file or stdin
        if sys.argv[1] == '-':
            # Read from stdin
            alerts_data = json.load(sys.stdin)
        else:
            # Read from file
            with open(sys.argv[1], 'r') as f:
                alerts_data = json.load(f)
        
        # Ensure we have a list of alerts
        if isinstance(alerts_data, dict):
            alerts = [alerts_data]
        else:
            alerts = alerts_data
        
        # Generate AI-enhanced summary
        summarizer = AdvancedIncidentSummarizer()
        summary = summarizer.generate_summary(alerts, include_historical)
        
        # Output JSON summary
        print(json.dumps(summary, indent=2))
        
    except Exception as e:
        logging.error(f"Error processing alerts: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
