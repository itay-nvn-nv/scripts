#!/usr/bin/env python3
import os
import random
import base64
from clearml import Task
from clearml.backend_api.session import Session

def setup_clearml_auth():
    webserver_url = os.getenv("WEBSERVER_URL")
    basic_auth = os.getenv("WEBSERVER_BASIC_AUTH")
    
    if not webserver_url or not basic_auth:
        raise ValueError("WEBSERVER_URL and WEBSERVER_BASIC_AUTH must be set")
    
    # Decode basic auth to get credentials
    try:
        credentials = base64.b64decode(basic_auth).decode('utf-8')
        access_key, secret_key = credentials.split(':')
    except Exception as e:
        raise ValueError(f"Invalid WEBSERVER_BASIC_AUTH format: {str(e)}")
    
    # Configure ClearML
    Session.set_credentials(
        api_server=webserver_url,
        web_server=webserver_url,
        files_server=webserver_url,
        access_key=access_key,
        secret_key=secret_key
    )
    
    # Verify authentication by making a test API call
    try:
        # Try to get the current user info as a verification
        user_info = Session.get_client().users.get_current_user()
        print(f"Authentication successful! Connected as: {user_info.name}")
    except Exception as e:
        raise ValueError(f"Authentication failed: {str(e)}")

def main():
    # Setup authentication first
    setup_clearml_auth()
    
    # Generate random names if not provided
    project_name = os.getenv("PROJECT_NAME", f"test-v{random.randint(0, 999):03d}")
    task_name = os.getenv("TASK_NAME", f"random-logger-v-{random.randint(0, 999):03d}")
    
    # Get required environment variables
    required_vars = [
        "WEBSERVER_URL",
        "WEBSERVER_BASIC_AUTH",
        "TASK_GIT_REPO",
        "TASK_GIT_BRANCH",
        "TASK_ENTRYPOINT",
        "TASK_IMAGE",
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Create or get project
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        print(f"PROJECT_ID is not set, creating new project: {project_name}")
        task = Task.create(
            project_name=project_name,
            task_name=task_name,
            task_type="training",
            repo=os.getenv("TASK_GIT_REPO"),
            branch=os.getenv("TASK_GIT_BRANCH"),
            script=os.getenv("TASK_ENTRYPOINT"),
            docker=os.getenv("TASK_IMAGE"),
            docker_args="-e CLEARML_AGENT_FORCE_TASK_INIT=1 -e CLEARML_AGENT_FORCE_POETRY",
            setup_shell_script=os.getenv("TASK_PRERUN_SCRIPT", ""),
        )
    else:
        print(f"Using existing project ID: {project_id}")
        task = Task.create(
            project_id=project_id,
            task_name=task_name,
            task_type="training",
            repo=os.getenv("TASK_GIT_REPO"),
            branch=os.getenv("TASK_GIT_BRANCH"),
            script=os.getenv("TASK_ENTRYPOINT"),
            docker=os.getenv("TASK_IMAGE"),
            docker_args="-e CLEARML_AGENT_FORCE_TASK_INIT=1 -e CLEARML_AGENT_FORCE_POETRY",
            setup_shell_script=os.getenv("TASK_PRERUN_SCRIPT", ""),
        )

    # Get queue name
    queue_name = os.getenv("QUEUE_NAME")
    if not queue_name:
        raise ValueError("QUEUE_NAME environment variable is required")

    # Enqueue task
    task.set_system_tags(["k8s"])
    task.execute_remotely(queue_name=queue_name)
    print(f"Task {task.id} enqueued to queue {queue_name}")

if __name__ == "__main__":
    main() 