import requests
import json
import subprocess
import sys
import os

API_TOKEN=os.getenv("NP_API_TOKEN")
CLUSTER_ID=os.getenv("NP_CLUSTER_ID")
BASE_URL=os.getenv("NP_BASE_URL")
np_key_base=os.getenv("NP_KEY_BASE") or "nature.gov/animal"
custom_role=os.getenv("NP_CUSTOM_ROLE") or "itay-worker"

url = f"{BASE_URL}/v1/k8s/clusters/{CLUSTER_ID}/node-pools"
auth_header=f"Bearer {API_TOKEN}"
headers = {'Authorization': auth_header, 'Content-Type': 'application/json'}
animals = ["owl", "falcon", "lion", "shark", "horse", "ostrich", "kangaroo", "dog", "horse", "jackrabbit", "coyote",
            "turtle", "hyena", "zebra", "snake", "dolphin", "gazelle", "rabbit", "panda", "monkey", "buck"]

# create a list of all non-ctrl-plane nodes
try:
    result = subprocess.run(
        ["kubectl", "get", "nodes", "-l", "!node-role.kubernetes.io/control-plane"],
        capture_output=True, text=True, check=True)
    lines = result.stdout.splitlines()[1:]  # Skip header line
    node_list = [line.split()[0] for line in lines]  # Extract node names (1st column)
    print(node_list)
except subprocess.CalledProcessError as e:
    print(f"Error occurred: {e}")
    sys.exit(1)

# for each listed node, label it with custom label + new role, then create a corresponding nodepool in runai
for i, node in enumerate(node_list, start=1):
    np_name=f"{animals[i]}-worker"
    np_key=np_key_base
    np_value=animals[i]

    custom_label=f"{np_key}={np_value}"
    role_label=f"node-role.kubernetes.io/{custom_role}=wow"
    try:
        print(f"Attempting to label node '{node}' with '{custom_label}' and '{role_label}'")
        # Run kubectl command to label the node
        result = subprocess.run(
            ["kubectl", "label", "node", node, custom_label, role_label, "--overwrite"],
            capture_output=True, text=True, check=True)

        print(f"Node '{node}' labeled successfully with '{custom_label}' and '{role_label}'")
    except subprocess.CalledProcessError as e:
        print(f"Failed to label node {node}: {e}")
        sys.exit(1)    
    print(f"Creating nodepool '{np_name}' in runai tenant (using label {np_key}={np_value})")
    payload = json.dumps({
    "name": np_name,
    "overProvisioningRatio": 1,
    "labelKey": np_key,
    "labelValue": np_value,
    "placementStrategy": {
        "cpu": "spread",
        "gpu": "binpack"}})

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)

# create project TBA
url = f"{BASE_URL}/api/v1/org-unit/projects"
auth_header=f"Bearer {API_TOKEN}"
headers = {'Authorization': auth_header, 'Content-Type': 'application/json'}

payload = json.dumps({
    "clusterId": CLUSTER_ID,
    "parentId": "4515890",
    "resources": [
        {
            "nodePool": {
                "name": "default",
                "id": "100025"
            },
            "gpu": {
                "deserved": 1,
                "limit": -1,
                "overQuotaWeight": 2
            },
            "cpu": {
                "deserved": None,
                "limit": -1,
                "overQuotaWeight": 2
            },
            "memory": {
                "deserved": None,
                "limit": -1,
                "overQuotaWeight": 2,
                "units": "Mib"
            }
        },
        {
            "nodePool": {
                "name": "mambo-number-2",
                "id": "100028"
            },
            "gpu": {
                "deserved": 1,
                "limit": -1,
                "overQuotaWeight": 2
            },
            "cpu": {
                "deserved": None,
                "limit": -1,
                "overQuotaWeight": 2
            },
            "memory": {
                "deserved": None,
                "limit": -1,
                "overQuotaWeight": 2,
                "units": "Mib"
            }
        },
        {
            "nodePool": {
                "name": "mambo-number-1",
                "id": "100027"
            },
            "gpu": {
                "deserved": 1,
                "limit": -1,
                "overQuotaWeight": 2
            },
            "cpu": {
                "deserved": None,
                "limit": -1,
                "overQuotaWeight": 2
            },
            "memory": {
                "deserved": None,
                "limit": -1,
                "overQuotaWeight": 2,
                "units": "Mib"
            }
        }
    ],
    "name": "my-test-project",
    "description": "",
    "defaultNodePools": [
        "mambo-number-1",
        "mambo-number-2",
        "default"
    ]
})
# response = requests.request("POST", url, headers=headers, data=payload)
# print(response.text)
