from runai.client import RunaiClient
import requests
import json
import subprocess
import sys

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

# saas "lots-o-nodes" cluster 2.13.60
API_TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJobVNxRklhNXlKcjF1REUzdmdHTUtkUWh2aHE1eGVuQVZrR1ZPMXRGX0U4In0.eyJleHAiOjE3Mjg5MDQ4NjgsImlhdCI6MTcyODkwMzA2OCwiYXV0aF90aW1lIjoxNzI4OTAzMDY2LCJqdGkiOiIyMWM1OWU1Mi1kNzE2LTRmNzItOTMwNi1hN2YzOGY2NjU0MDEiLCJpc3MiOiJodHRwczovL2FwcC5ydW4uYWkvYXV0aC9yZWFsbXMvZW52aW5hY2xpY2siLCJhdWQiOlsicnVuYWktYWRtaW4tdWkiLCJydW5haSJdLCJzdWIiOiJkZXZvcHNAcnVuLmFpIiwidHlwIjoiSUQiLCJhenAiOiJydW5haS1hZG1pbi11aSIsInNlc3Npb25fc3RhdGUiOiI3Zjg1NTA3Ni02NjRkLTRkMDYtODdjMy0xOWUyNDQwZmVhNmEiLCJhdF9oYXNoIjoiS2oyOGNzRXY3ZFlTUnFjOExkMnFQdyIsInNpZCI6IjdmODU1MDc2LTY2NGQtNGQwNi04N2MzLTE5ZTI0NDBmZWE2YSIsInRlbmFudF9pZCI6MjEyLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwic3ViamVjdF91dWlkIjoiYzk0OGNlMTEtM2JhOC00ZjlhLThjN2ItMDU4OWI5ZDkyOThkIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiZGV2b3BzQHJ1bi5haSIsImVtYWlsIjoiZGV2b3BzQHJ1bi5haSJ9.G2798oxxx9jWpXRezxhkKnYD9gZdVxV6o-W1Gij5boAcXelvh6vPcOL-WQRRLEqGInWUj28bBJJt7FI1CLUXXrud6HjUQwN0HgG6XM_WxqQyz9xiFtcyDDlweyyfoVfSyzaK2QwykiTtAQOsZatUQ08AbVtC-pIKG4oHNSxLlFsSDFNnBV8_UUILgPLa37PtEwCWs21RGY__6-vPeAHFMkdFhfO_ihd3mGHs31pRcCqByOv35YalSTscsaVMijj5jzR9Mda42QBDu-DLD4dXfH12N5-UTYnpWhJ0mqWLIGulHulINMOlVLL0CVz8trULoFha_chob5PKQFfit7VEhg"
CLUSTER_ID="c0be7a2d-f0d7-4c3c-a5d9-71961f918b96"
BASE_URL="https://envinaclick.run.ai"

# # self-hosted "usaa" cluster 2.17.33
# API_TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJoS29OUU45X19mRXVzVzExZzhDdHdIYTlPcWplcl9mcDNqTC1pNkdlaV84In0.eyJleHAiOjE3Mjg5MDQ5NDksImlhdCI6MTcyODkwNDA0OSwiYXV0aF90aW1lIjoxNzI4OTA0MDQ4LCJqdGkiOiI3NmU0OTYwYy04ZGYyLTRhM2QtOWM0NC1mMjQyNTI0NDFjM2YiLCJpc3MiOiJodHRwczovL3VzYWEtMjE3MzMtc2gucnVuYWlsYWJzLWNzLmNvbS9hdXRoL3JlYWxtcy9ydW5haSIsImF1ZCI6WyJydW5haS1hZG1pbi11aSIsInJ1bmFpIl0sInN1YiI6InRlc3RAcnVuLmFpIiwidHlwIjoiSUQiLCJhenAiOiJydW5haS1hZG1pbi11aSIsInNlc3Npb25fc3RhdGUiOiJhMzAyYjgxMy05N2U1LTRlOGUtYmM3Yi0wMGZmMjY4OGQ2YjQiLCJhdF9oYXNoIjoiNUNjcUxjLVBhQmZ5OGpZYlpDQmlhQSIsImFjciI6IjEiLCJzaWQiOiJhMzAyYjgxMy05N2U1LTRlOGUtYmM3Yi0wMGZmMjY4OGQ2YjQiLCJ0ZW5hbnRfaWQiOjEwMDEsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJzdWJqZWN0X3V1aWQiOiJhZDI0ZGU0Yi1mMmNlLTQ2NTYtOThhNS0xNTE1MzViNDI2ZDAiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJ0ZXN0QHJ1bi5haSIsImVtYWlsIjoidGVzdEBydW4uYWkifQ.bJUVoI-ro8C1LqDkNunKflnxDRuDtA62S2Npdd_OM06W_Vvr5yzu0MjlSYtm10gpdP397v0Bfho65G9R1W18UtaNIAQBGphlYqXAuQwWN_6WkUB53OqZgQ8WmkMhzkTImXfJHfIIHPAL4n6oG009r2QY3RGkj6Mw5-qYcP4DK2hFRDXLqUMwkLh3ACWRtTbhnJaeYi1rOOYtZ9xxqcD__nl_SB1X6bWpJCmFqmpGdvDO5EfQ-_SVdrmV4xWmb1GsdOpoTShav03BsEAQqGwJutwqRChkkzfA-5uEwL_-8UvsjLz-x7eERr_Se8BD9Onc2KKyBnLA6P7B_ys03kb-sA"
# CLUSTER_ID="6d417e03-e0c4-4f91-bb40-87eff57e818d"
# BASE_URL="https://usaa-21733-sh.runailabs-cs.com"

np_name_base="mambo-number"
np_key_base="itay.lolz/mambo"
np_value_base="number"
custom_role="itay-worker"

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

## using runapy (doesnt work)
# client = RunaiClient(
#     bearer_token=API_TOKEN,
#     runai_base_url=BASE_URL,
#     cluster_id=CLUSTER_ID,
#     debug=True
# )
#
# for node in node_list:
#     i += 1
#     name=f"mambo-numba-{i}"
#     label_key="itay.lolz/mambo"
#     label_value=f"numba-{i}"
#     print(name, label_key, label_value)
#     print(client.node_pools.create(name=name, label_key=label_key, label_value=label_value, placement_strategy={"cpu": "spread", "gpu": "spread"}, over_provisioning_ratio=0))

# # api curl command:
# curl -X POST "https://usaa-21733-sh.runailabs-cs.com/v1/k8s/clusters/6d417e03-e0c4-4f91-bb40-87eff57e818d/node-pools" \
#   -H "Authorization: Bearer eyxxxxxxx" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "name": "mambo-number-5",
#     "overProvisioningRatio": 1,
#     "labelKey": "itay.lolz/mambo",
#     "labelValue": "number-5",
#     "placementStrategy": {
#       "cpu": "spread",
#       "gpu": "binpack"
#     }
#   }'

url = f"{BASE_URL}/v1/k8s/clusters/{CLUSTER_ID}/node-pools"

auth_header=f"Bearer {API_TOKEN}"

headers = {
  'Authorization': auth_header,
  'Content-Type': 'application/json'
}

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
