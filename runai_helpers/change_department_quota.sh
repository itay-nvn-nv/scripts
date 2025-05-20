# change the "default" departments' GPU quota to 0

# provide inputs for the following vars:
# (the token is taken from the CLU config by default, assuming runai CLI v2 is installed and logged in - but can be explicitly set otherwise)
RUNAI_CTRL_PLANE=""
TOKEN=$(cat ~/.runai/authentication.json | jq -r .'accessToken' | base64 -d)
CLUSTER_NAME=""
DESIRED_GPU_QUOTA=0 # integer, not string

# leave the following untouched:
CLUSTER_UUID=$(curl -s "$RUNAI_CTRL_PLANE/api/v1/clusters" \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H "authorization: Bearer $TOKEN" | jq -r ".[] | select(.name == \"$CLUSTER_NAME\") | .uuid")

echo "Cluster name: $CLUSTER_NAME"
echo "Cluster UUID: $CLUSTER_UUID"
echo

DEPARTMENT_NAME="default"

DEPARTMENT_ID=$(curl -s "$RUNAI_CTRL_PLANE/api/v1/org-unit/departments" \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H "authorization: Bearer $TOKEN" | jq -r ".departments[] | select(.name == \"$DEPARTMENT_NAME\" and .clusterId == \"$CLUSTER_UUID\") | .id")

echo "Department name: $DEPARTMENT_NAME"
echo "Department ID: $DEPARTMENT_ID"
echo

DEPARTMENT_SETTINGS_CURRENT=$(curl -s "$RUNAI_CTRL_PLANE/api/v1/org-unit/departments/$DEPARTMENT_ID" \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H "authorization: Bearer $TOKEN" | jq)

NODEPOOL_NAME="default"
NODEPOOL_ID=$(echo $DEPARTMENT_SETTINGS_CURRENT | jq -r ".resources[] | select(.nodePool.name == \"$NODEPOOL_NAME\") | .nodePool.id")
echo "Nodepool name: $NODEPOOL_NAME"
echo "Nodepool ID: $NODEPOOL_ID"
echo

echo "Current GPU quota: $(echo $DEPARTMENT_SETTINGS_CURRENT | jq -r '.resources[] | select(.nodePool.name == "default") | .gpu.deserved')"
echo "Changing GPU quota to $DESIRED_GPU_QUOTA..."
echo

curl -s "$RUNAI_CTRL_PLANE/api/v1/org-unit/departments/$DEPARTMENT_ID/resources" \
  -X 'PATCH' \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  --data-raw "[{\"nodePool\": {\"id\": \"$NODEPOOL_ID\"}, \"gpu\": {\"deserved\": $DESIRED_GPU_QUOTA}}]" | jq
# succesful change will output the new department settings with the new value set in "nodePool.gpu.deseverd"