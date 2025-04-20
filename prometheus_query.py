#!/usr/bin/env python3
# pip install requests, pygments
# python3 prometheus_query.py --url http://prometheus-operator.monitoring.svc.cluster.local:9090 --query 'up' --export
import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import urllib.parse
import argparse
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter

class PrometheusQuery:
    def __init__(self, base_url: str):
        """
        Initialize the PrometheusQuery client.
        
        Args:
            base_url (str): The base URL of your Prometheus server (e.g., 'http://localhost:9090')
        """
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/v1"

    def _validate_query(self, query: str) -> None:
        """
        Validate the PromQL query format.
        
        Args:
            query (str): The PromQL query to validate
            
        Raises:
            ValueError: If the query is empty or invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Basic validation for metric name and labels
        if '{' in query and '}' in query:
            # Check if labels are properly formatted
            if not query.count('{') == query.count('}'):
                raise ValueError("Mismatched curly braces in query")
            
            # Check if label values are properly quoted
            if '"' in query:
                if query.count('"') % 2 != 0:
                    raise ValueError("Mismatched quotes in query")

    def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an instant query against Prometheus.
        
        Args:
            query (str): The PromQL query to execute (e.g., 'runai_gpu_memory_used_mebibytes_per_workload{workload_name="shared-inpaint-creative-inference"}')
            params (dict, optional): Additional query parameters
            
        Returns:
            dict: The query response from Prometheus
        """
        self._validate_query(query)
        endpoint = f"{self.api_url}/query"
        default_params = {'query': query}
        if params:
            default_params.update(params)
            
        try:
            # Let requests handle the URL encoding
            response = requests.get(endpoint, params=default_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to execute query: {str(e)}")

    def query_range(self, query: str, start: datetime, end: datetime, 
                   step: str = '1m', params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a range query against Prometheus.
        
        Args:
            query (str): The PromQL query to execute
            start (datetime): Start time for the query range
            end (datetime): End time for the query range
            step (str): Query resolution step width (e.g., '1m', '5m', '1h')
            params (dict, optional): Additional query parameters
            
        Returns:
            dict: The query response from Prometheus
        """
        self._validate_query(query)
        endpoint = f"{self.api_url}/query_range"
        default_params = {
            'query': query,
            'start': start.timestamp(),
            'end': end.timestamp(),
            'step': step
        }
        if params:
            default_params.update(params)
            
        try:
            # Let requests handle the URL encoding
            response = requests.get(endpoint, params=default_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to execute range query: {str(e)}")

def parse_args():
    parser = argparse.ArgumentParser(description='Query Prometheus API')
    parser.add_argument('--query', type=str, required=True, help='PromQL query to execute')
    parser.add_argument('--url', type=str, default='http://localhost:9090', help='Prometheus server URL')
    parser.add_argument('--range', action='store_true', help='Execute a range query instead of an instant query')
    parser.add_argument('--start', type=str, help='Start time for range query (ISO format, e.g., 2023-01-01T00:00:00Z)')
    parser.add_argument('--end', type=str, help='End time for range query (ISO format, e.g., 2023-01-01T01:00:00Z)')
    parser.add_argument('--step', type=str, default='1m', help='Step width for range query (e.g., 1m, 5m, 1h)')
    parser.add_argument('--no-color', action='store_true', help='Disable syntax highlighting')
    parser.add_argument('--export', action='store_true', help='Export the query result to a JSON file in /tmp folder')
    return parser.parse_args()

def main():
    args = parse_args()
    prom = PrometheusQuery(args.url)
    
    try:
        if args.range:
            # Parse start and end times
            start_time = datetime.fromisoformat(args.start.replace('Z', '+00:00')) if args.start else datetime.now() - timedelta(hours=1)
            end_time = datetime.fromisoformat(args.end.replace('Z', '+00:00')) if args.end else datetime.now()
            
            result = prom.query_range(args.query, start_time, end_time, step=args.step)
            print("\nRange Query Result:")
        else:
            result = prom.query(args.query)
            print("\nInstant Query Result:")
        
        # Display query information
        print("\nQuery Information:")
        print(f"Query: {args.query}")
        if args.range:
            print(f"Start Time: {start_time.isoformat()}")
            print(f"End Time: {end_time.isoformat()}")
            print(f"Step: {args.step}")
        
        # Display result with syntax highlighting
        print("\nResult:")
        json_str = json.dumps(result, indent=2)
        if not args.no_color:
            highlighted_json = highlight(json_str, JsonLexer(), TerminalFormatter())
            print(highlighted_json)
        else:
            print(json_str)
        
        # Export the result to a JSON file if requested
        if args.export:
            # Generate filename with HH-MM-SS_DD-MM-YY.json format
            timestamp = datetime.now().strftime("%H-%M-%S_%d-%m-%y")
            filename = f"/tmp/prometheus_query_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\nQuery result exported to: {filename}")
    except Exception as e:
        print(f"Error executing query: {e}")

if __name__ == "__main__":
    main() 