#!/usr/bin/env python3

import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class PrometheusQuery:
    def __init__(self, base_url: str):
        """
        Initialize the PrometheusQuery client.
        
        Args:
            base_url (str): The base URL of your Prometheus server (e.g., 'http://localhost:9090')
        """
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/v1"

    def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an instant query against Prometheus.
        
        Args:
            query (str): The PromQL query to execute
            params (dict, optional): Additional query parameters
            
        Returns:
            dict: The query response from Prometheus
        """
        endpoint = f"{self.api_url}/query"
        default_params = {'query': query}
        if params:
            default_params.update(params)
            
        try:
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
            response = requests.get(endpoint, params=default_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to execute range query: {str(e)}")

def main():
    # Example usage
    prom = PrometheusQuery('http://localhost:9090')
    
    # Example instant query
    try:
        result = prom.query('up')
        print("Instant Query Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error executing instant query: {e}")
    
    # Example range query
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        result = prom.query_range('rate(http_requests_total[5m])', 
                                start_time, end_time, step='5m')
        print("\nRange Query Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error executing range query: {e}")

if __name__ == "__main__":
    main() 