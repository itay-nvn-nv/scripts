#!/usr/bin/env python3

import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import urllib.parse

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
            # URL encode the query to handle special characters
            encoded_params = {k: urllib.parse.quote(str(v)) if k == 'query' else v 
                            for k, v in default_params.items()}
            response = requests.get(endpoint, params=encoded_params)
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
            # URL encode the query to handle special characters
            encoded_params = {k: urllib.parse.quote(str(v)) if k == 'query' else v 
                            for k, v in default_params.items()}
            response = requests.get(endpoint, params=encoded_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to execute range query: {str(e)}")

def main():
    # Example usage
    prom = PrometheusQuery('http://localhost:9090')
    
    # Example with the simple query
    try:
        simple_query = 'runai_gpu_memory_used_mebibytes_per_workload{workload_name="shared-inpaint-creative-inference"}'
        print(f"\nExecuting simple query: {simple_query}")
        result = prom.query(simple_query)
        print("Simple Query Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error executing simple query: {e}")
    
    # Example with the complex query
    try:
        complex_query = '''sum by (workload_name, workload_id, pod_group_uuid, job_name, job_uuid , pod_namespace, project) 
        (label_replace(label_replace(sum(rate(container_cpu_usage_seconds_total{ container!=""}[2m])) by (pod, namespace),
        "pod_name" , "bla", "pod", "(.*)"), "pod_namespace" , "bla", "namespace", "(.*)") 
        * on(pod_name, pod_namespace) group_left(workload_name, pod_group_uuid, job_name, job_uuid, workload_id, project) 
        (runai_pod_phase_with_info{phase="Running"} ==1))'''
        
        print(f"\nExecuting complex query: {complex_query}")
        result = prom.query(complex_query)
        print("Complex Query Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error executing complex query: {e}")
    
    # Example range query with the complex metric
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        result = prom.query_range(complex_query, start_time, end_time, step='5m')
        print("\nComplex Query Range Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error executing complex range query: {e}")

if __name__ == "__main__":
    main() 