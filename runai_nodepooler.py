from runai.client import RunaiClient
import requests
import json
import subprocess
import sys

API_TOKEN="eyxxxxx"
CLUSTER_ID=""
BASE_URL="https://envinaclick.run.ai"

np_name_base="mambo-number"
np_key_base="itay.lolz/mambo"
np_value_base="number"
custom_role="itay-worker"

# check if kubectl is installed
try:
    # Run 'kubectl version --client' to check if kubectl is available
    result = subprocess.run(['kubectl', 'version', '--client'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # If kubectl is installed, the return code will be 0
    if result.returncode == 0:
        print("kubectl is installed.")
    else:
        print("kubectl is not installed.")
        sys.exit(1)  # Exit the script if kubectl is not installed

except FileNotFoundError:
    # kubectl command not found
    print("kubectl is not installed or not in PATH.")
    sys.exit(1)

# get nodes with "runai-system" role
try:
    # Run kubectl command to get all nodes with the specified role
    result = subprocess.run(
        ["kubectl", "get", "nodes", "-l", f"node-role.kubernetes.io/runai-system"],
        capture_output=True, text=True, check=True
    )

    # Split the output by lines and extract node names (ignoring the header line)
    lines = result.stdout.splitlines()[1:]  # Skip header line
    node_list = [line.split()[0] for line in lines]  # Extract node names (1st column)
    print(node_list)

except subprocess.CalledProcessError as e:
    print(f"Error occurred: {e}")
    sys.exit(1)

# label the nodes with custom label and new role
for i, node in enumerate(node_list, start=1):

    np_name=f"{np_name_base}-{i}"
    np_key=np_key_base
    np_value=f"{np_value_base}-{i}"

    custom_label=f"{np_key}={np_value}"
    role_label=f"node-role.kubernetes.io/{custom_role}=wow",

    try:
        # Run kubectl command to label the node
        result = subprocess.run(
            ["kubectl", "label", "node", node, custom_label, role_label, "--overwrite"],
            capture_output=True, text=True, check=True)

        print(f"Node '{node}' labeled successfully with '{custom_label}' and '{role_label}'")
    except subprocess.CalledProcessError as e:
        print(f"Failed to label node {node}: {e}")

url = f"{BASE_URL}/v1/k8s/clusters/{CLUSTER_ID}/node-pools"

auth_header=f"Bearer {API_TOKEN}"

headers = {
  'Authorization': auth_header,
  'Content-Type': 'application/json'
}

# create nodepools
for i, node in enumerate(node_list, start=1):
    np_name=f"{np_name_base}-{i}"
    np_key=np_key_base
    np_value=f"{np_value_base}-{i}"
    payload = json.dumps({
    "name": np_name,
    "overProvisioningRatio": 1,
    "labelKey": np_key,
    "labelValue": np_value,
    "placementStrategy": {
        "cpu": "spread",
        "gpu": "binpack"
    }
    })

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)

# create project
