#!/usr/bin/env python3

import os
import json
import random
import requests
import time
import logging
from typing import Optional, Dict, Any, List


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_random_suffix() -> str:
    """Generate a random 3-digit suffix."""
    return f"{random.randint(0, 999):03d}"


class ClearMLClient:
    def __init__(self, webserver_url: str, basic_auth: str, debug: bool = False):
        self.webserver_url = webserver_url
        self.basic_auth = basic_auth
        self.token = None
        self.headers = {}
        
        if debug:
            # Enable request/response debugging
            import http.client as http_client
            http_client.HTTPConnection.debuglevel = 1
            requests_log = logging.getLogger("requests.packages.urllib3")
            requests_log.setLevel(logging.DEBUG)
            requests_log.propagate = True

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
        
        logger.info(f"Authenticating with ClearML server at {self.webserver_url}")
        response = requests.post(login_url, headers=headers)
        response.raise_for_status()
        
        self.token = response.json()["data"]["token"]
        self.headers = {
            "Cookie": f"clearml-token-k8s={self.token}",
            "Content-Type": "application/json"
        }
        
        logger.info("Authentication successful - token received")
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
        
        logger.info(f"Creating project '{project_name}'")
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        project_id = response.json()["data"]["id"]
        logger.info(f"Created project '{project_name}' with ID: {project_id}")
        return project_id
    
    def get_all_queues(self) -> List[Dict[str, Any]]:
        """Get all available queues."""
        url = f"{self.webserver_url}/api/v2.30/queues.get_all"
        
        logger.info("Retrieving all available queues")
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        queues = response.json()["data"]["queues"]
        logger.info(f"Found {len(queues)} queues")
        return queues
    
    def get_queue_id(self, queue_name: str) -> Optional[str]:
        """Check if queue exists and return its ID if found."""
        queues = self.get_all_queues()
        for queue in queues:
            if queue["name"] == queue_name:
                logger.info(f"Found existing queue '{queue_name}' with ID: {queue['id']}")
                return queue["id"]
        logger.info(f"Queue '{queue_name}' not found")
        return None
    
    def create_queue(self, queue_name: str) -> str:
        """Create a new queue and return its ID."""
        url = f"{self.webserver_url}/api/v2.30/queues.create"
        data = {"name": queue_name}
        
        logger.info(f"Creating queue '{queue_name}'")
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        queue_id = response.json()["data"]["id"]
        logger.info(f"Created queue '{queue_name}' with ID: {queue_id}")
        return queue_id
    
    def create_task(self, task_config: Dict[str, Any]) -> str:
        """Create a new task and return its ID."""
        url = f"{self.webserver_url}/api/v2.30/tasks.create"
        
        logger.info(f"Creating task '{task_config['name']}'")
        response = requests.post(url, headers=self.headers, json=task_config)
        response.raise_for_status()
        
        task_id = response.json()["data"]["id"]
        logger.info(f"Created task '{task_config['name']}' with ID: {task_id}")
        return task_id
    
    def update_task(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update task properties."""
        url = f"{self.webserver_url}/api/v2.30/tasks.edit"
        payload = {
            "task": task_id,
            **data
        }
        
        logger.info(f"Updating task {task_id} with new properties: {json.dumps(data)}")
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        logger.info(f"Updated task {task_id}")
        return response.json()
    
    def reset_task(self, task_id: str) -> Dict[str, Any]:
        """Reset task status to 'created'."""
        url = f"{self.webserver_url}/api/v2.30/tasks.reset"
        data = {"task": task_id}
        
        logger.info(f"Resetting task {task_id}")
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        logger.info(f"Reset task {task_id}")
        return response.json()
    
    def stop_task(self, task_id: str) -> Dict[str, Any]:
        """Stop a running task."""
        url = f"{self.webserver_url}/api/v2.30/tasks.stop"
        data = {"task": task_id}
        
        logger.info(f"Stopping task {task_id}")
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        logger.info(f"Stopped task {task_id}")
        return response.json()
    
    def enqueue_task(self, queue_id: str, task_id: str) -> Dict[str, Any]:
        """Enqueue a task and return the response."""
        # First ensure the task is not already queued somewhere else
        task_info = self.get_task_info(task_id)
        current_status = task_info.get("status")
        
        # If the task is already queued, reset it first
        if current_status in ["queued", "in_progress"]:
            logger.info(f"Task is already {current_status}, resetting it first")
            try:
                self.stop_task(task_id)
                self.reset_task(task_id)
            except requests.exceptions.HTTPError as e:
                logger.warning(f"Could not reset task: {e}")
        
        # Set the queue directly in the task
        logger.info(f"Setting execution queue to {queue_id} for task {task_id}")
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
        
        logger.info(f"Enqueueing task {task_id} to queue {queue_id}")
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        logger.info(f"Task {task_id} enqueued to queue {queue_id}")
        return response.json()
    
    def get_task_info(self, task_id: str) -> Dict[str, Any]:
        """Get detailed information about a task."""
        url = f"{self.webserver_url}/api/v2.30/tasks.get_all"
        data = {"id": [task_id]}
        
        logger.info(f"Getting info for task {task_id}")
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        tasks = response.json()["data"]["tasks"]
        if not tasks:
            raise ValueError(f"Task {task_id} not found")
        
        return tasks[0]
    
    def get_task_status(self, task_id: str) -> str:
        """Get the status of a task."""
        task_info = self.get_task_info(task_id)
        status = task_info.get("status", "unknown")
        
        logger.info(f"Task {task_id} status: {status}")
        return status
    
    def wait_for_task_to_start(self, task_id: str, timeout: int = 60, poll_interval: int = 5) -> str:
        """Wait for a task to start and return its final status."""
        start_time = time.time()
        last_status = None
        
        logger.info(f"Waiting up to {timeout} seconds for task {task_id} to start")
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            last_status = status
            
            if status in ["failed", "completed", "in_progress"]:
                logger.info(f"Task reached final status: {status}")
                break
                
            logger.info(f"Current status: {status}. Checking again in {poll_interval} seconds...")
            time.sleep(poll_interval)
        
        if time.time() - start_time >= timeout:
            logger.warning(f"Timeout reached while waiting for task to start. Last status: {last_status}")
        
        return last_status


def main():
    # Get environment variables with defaults
    webserver_url = os.environ.get("WEBSERVER_URL")
    webserver_basic_auth = os.environ.get("WEBSERVER_BASIC_AUTH")
    debug_mode = os.environ.get("DEBUG", "false").lower() == "true"
    
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
    client = ClearMLClient(webserver_url, webserver_basic_auth, debug=debug_mode)
    
    # 1. Login and get token
    client.login()
    
    # 2. Get or create project
    if not project_id:
        project_id = client.create_project(project_name)
    else:
        logger.info(f"Using existing project ID: {project_id}")
    
    # 3. Get or create queue
    if not queue_id:
        queue_id = client.get_queue_id(queue_name)
        if not queue_id:
            queue_id = client.create_queue(queue_name)
        else:
            logger.info(f"Using existing queue '{queue_name}' with ID: {queue_id}")
    else:
        logger.info(f"Using existing queue ID: {queue_id}")
    
    # Display all available queues for debugging
    if debug_mode:
        all_queues = client.get_all_queues()
        logger.info("Available queues:")
        for q in all_queues:
            logger.info(f"  - {q['name']} (ID: {q['id']})")
    
    # 4. Create task without setting the execution queue yet
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
        # First explicitly set the execution queue in the task
        client.update_task(task_id, {
            "execution": {
                "queue": queue_id
            }
        })
        
        # Then enqueue the task
        client.enqueue_task(queue_id, task_id)
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error enqueueing task: {e}")
        if debug_mode:
            logger.error(f"Response: {e.response.text}")
        # Try to retrieve the current task status anyway
        try:
            client.get_task_status(task_id)
        except Exception as e2:
            logger.error(f"Could not get task status: {e2}")
    
    # 6. Wait for task to start if requested
    final_status = None
    if wait_for_task:
        try:
            final_status = client.wait_for_task_to_start(task_id, timeout=wait_timeout)
        except Exception as e:
            logger.error(f"Error while waiting for task to start: {e}")
            final_status = "unknown"
    else:
        # Just check the status once
        try:
            final_status = client.get_task_status(task_id)
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            final_status = "unknown"
    
    logger.info(f"\nWorkflow complete:")
    logger.info(f"  Project: {project_name} (ID: {project_id})")
    logger.info(f"  Queue: {queue_name} (ID: {queue_id})")
    logger.info(f"  Task: {task_name} (ID: {task_id})")
    logger.info(f"  Status: {final_status}")


if __name__ == "__main__":
    main() 