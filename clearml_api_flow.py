#!/usr/bin/env python3

import os
import json
import random
import requests
import time
from typing import Optional, Dict, Any


def generate_random_suffix() -> str:
    """Generate a random 3-digit suffix."""
    return f"{random.randint(0, 999):03d}"


class ClearMLClient:
    def __init__(self, webserver_url: str, basic_auth: str):
        self.webserver_url = webserver_url
        self.basic_auth = basic_auth
        self.token = None
        self.headers = {}

    def login(self) -> str:
        """Authenticate with ClearML server and get token."""
        login_url = f"{self.webserver_url}/api/v2.30/auth.login"
        headers = {
            "Authorization": f"Basic {self.basic_auth}",
            "Origin": self.webserver_url,
            "Referer": f"{self.webserver_url}/login",
            "X-Allegro-Client": "Webapp-1.16.2-502",
            "X-Clearml-Impersonate-As": "__tests__"
        }
        
        response = requests.post(login_url, headers=headers)
        response.raise_for_status()
        
        self.token = response.json()["data"]["token"]
        self.headers = {
            "Cookie": f"clearml-token-k8s={self.token}",
            "Content-Type": "application/json"
        }
        
        print(f"Authenticated with ClearML - token received")
        return self.token
    
    def create_project(self, project_name: str) -> str:
        """Create a new project and return its ID."""
        url = f"{self.webserver_url}/api/v2.30/projects.create"
        data = {
            "name": project_name,
            "description": "test in progress",
            "system_tags": [],
            "default_output_destination": None
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        project_id = response.json()["data"]["id"]
        print(f"Created project '{project_name}' with ID: {project_id}")
        return project_id
    
    def get_queue_id(self, queue_name: str) -> Optional[str]:
        """Check if queue exists and return its ID if found."""
        url = f"{self.webserver_url}/api/v2.30/queues.get_all"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        queues = response.json()["data"]["queues"]
        for queue in queues:
            if queue["name"] == queue_name:
                return queue["id"]
        return None
    
    def create_queue(self, queue_name: str) -> str:
        """Create a new queue and return its ID."""
        url = f"{self.webserver_url}/api/v2.30/queues.create"
        data = {"name": queue_name}
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        queue_id = response.json()["data"]["id"]
        print(f"Created queue '{queue_name}' with ID: {queue_id}")
        return queue_id
    
    def create_task(self, task_config: Dict[str, Any]) -> str:
        """Create a new task and return its ID."""
        url = f"{self.webserver_url}/api/v2.30/tasks.create"
        
        response = requests.post(url, headers=self.headers, json=task_config)
        response.raise_for_status()
        
        task_id = response.json()["data"]["id"]
        print(f"Created task '{task_config['name']}' with ID: {task_id}")
        return task_id
    
    def update_task(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update task properties."""
        url = f"{self.webserver_url}/api/v2.30/tasks.edit"
        payload = {
            "task": task_id,
            **data
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        print(f"Updated task {task_id} with new properties")
        return response.json()
    
    def enqueue_task(self, queue_id: str, task_id: str) -> Dict[str, Any]:
        """Enqueue a task and return the response."""
        # First, set the execution queue in the task itself
        self.update_task(task_id, {
            "execution": {
                "queue": queue_id
            }
        })
        
        # Then enqueue the task
        url = f"{self.webserver_url}/api/v2.30/tasks.enqueue"
        data = {
            "queue": queue_id,
            "task": task_id
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        print(f"Task {task_id} enqueued to queue {queue_id}")
        return response.json()
    
    def get_task_status(self, task_id: str) -> str:
        """Get the status of a task."""
        url = f"{self.webserver_url}/api/v2.30/tasks.get_all"
        data = {"id": [task_id]}
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        task_status = response.json()["data"]["tasks"][0]["status"]
        print(f"Task {task_id} status: {task_status}")
        return task_status
    
    def wait_for_task_to_start(self, task_id: str, timeout: int = 60, poll_interval: int = 5) -> str:
        """Wait for a task to start and return its final status."""
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            last_status = status
            
            if status in ["failed", "completed", "in_progress"]:
                break
                
            print(f"Waiting for task to start. Current status: {status}. Checking again in {poll_interval} seconds...")
            time.sleep(poll_interval)
        
        return last_status


def main():
    # Get environment variables with defaults
    webserver_url = os.environ.get("WEBSERVER_URL")
    webserver_basic_auth = os.environ.get("WEBSERVER_BASIC_AUTH")
    
    # Check for required environment variables
    if not webserver_url or not webserver_basic_auth:
        raise ValueError("WEBSERVER_URL and WEBSERVER_BASIC_AUTH environment variables are required")
    
    # Project and queue settings
    project_id = os.environ.get("PROJECT_ID")
    queue_id = os.environ.get("QUEUE_ID")
    project_name = os.environ.get("PROJECT_NAME", f"test-v{generate_random_suffix()}")
    queue_name = os.environ.get("QUEUE_NAME")
    
    # Task settings
    task_name = os.environ.get("TASK_NAME", f"random-logger-v-{generate_random_suffix()}")
    task_git_repo = os.environ.get("TASK_GIT_REPO")
    task_git_branch = os.environ.get("TASK_GIT_BRANCH")
    task_entrypoint = os.environ.get("TASK_ENTRYPOINT")
    task_image = os.environ.get("TASK_IMAGE")
    task_prerun_script = os.environ.get("TASK_PRERUN_SCRIPT")
    
    # Optional: Wait for task to start
    wait_for_task = os.environ.get("WAIT_FOR_TASK", "false").lower() == "true"
    wait_timeout = int(os.environ.get("WAIT_TIMEOUT", "60"))
    
    # Check for required task settings
    if not all([queue_name, task_git_repo, task_git_branch, task_entrypoint, task_image]):
        missing = []
        for var_name, var_value in {
            "QUEUE_NAME": queue_name,
            "TASK_GIT_REPO": task_git_repo,
            "TASK_GIT_BRANCH": task_git_branch,
            "TASK_ENTRYPOINT": task_entrypoint,
            "TASK_IMAGE": task_image
        }.items():
            if not var_value:
                missing.append(var_name)
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    # Initialize ClearML client
    client = ClearMLClient(webserver_url, webserver_basic_auth)
    
    # 1. Login and get token
    client.login()
    
    # 2. Get or create project
    if not project_id:
        project_id = client.create_project(project_name)
    else:
        print(f"Using existing project ID: {project_id}")
    
    # 3. Get or create queue
    if not queue_id:
        queue_id = client.get_queue_id(queue_name)
        if not queue_id:
            queue_id = client.create_queue(queue_name)
        else:
            print(f"Using existing queue '{queue_name}' with ID: {queue_id}")
    else:
        print(f"Using existing queue ID: {queue_id}")
    
    # 4. Create task - note that we're not setting execution.queue here
    # to avoid the conflict when enqueuing
    task_config = {
        "project": project_id,
        "name": task_name,
        "type": "training",
        "script": {
            "repository": task_git_repo,
            "branch": task_git_branch,
            "working_dir": ".",
            "entry_point": task_entrypoint,
            "requirements": None
        },
        "hyperparams": {
            "Args": {}
        },
        "container": {
            "image": task_image,
            "arguments": "-e CLEARML_AGENT_FORCE_TASK_INIT=1 -e CLEARML_AGENT_FORCE_POETRY",
            "setup_shell_script": task_prerun_script
        }
    }
    
    task_id = client.create_task(task_config)
    
    # 5. Enqueue task (this will also update the task with the queue)
    try:
        client.enqueue_task(queue_id, task_id)
    except requests.exceptions.HTTPError as e:
        print(f"Error enqueueing task: {e}")
        # Try to retrieve the current task status anyway
        client.get_task_status(task_id)
    
    # 6. Wait for task to start if requested
    final_status = None
    if wait_for_task:
        print(f"Waiting up to {wait_timeout} seconds for task to start...")
        final_status = client.wait_for_task_to_start(task_id, timeout=wait_timeout)
    else:
        # Just check the status once
        final_status = client.get_task_status(task_id)
    
    print(f"\nWorkflow complete:")
    print(f"  Project: {project_name} (ID: {project_id})")
    print(f"  Queue: {queue_name} (ID: {queue_id})")
    print(f"  Task: {task_name} (ID: {task_id})")
    print(f"  Status: {final_status}")


if __name__ == "__main__":
    main() 