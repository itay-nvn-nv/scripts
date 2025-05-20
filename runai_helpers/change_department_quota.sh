# script for changing the "default" departments' GPU quota to 0 (from the default "-1")

### provide inputs for the following vars:
CLUSTER_NAME=""
RUNAI_CTRL_PLANE=""
RUNAI_USERNAME="" # use the pre-existing local user credentials
RUNAI_PASSWORD="" # use the pre-existing local user credentials

### Do not modify anything below this line.
RUNAI_TOKEN=$(curl -s -X POST "$RUNAI_CTRL_PLANE/api/v1/token" \
  --header 'Accept: */*' \
  --header 'Content-Type: application/json' \
   --data-raw "{\"grantType\": \"password\", \"clientID\": \"cli\", \"username\": \"$RUNAI_USERNAME\", \"password\": \"$RUNAI_PASSWORD\"}" | jq -r .accessToken)

CLUSTER_UUID=$(curl -s "$RUNAI_CTRL_PLANE/api/v1/clusters" \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H "authorization: Bearer $RUNAI_TOKEN" | jq -r ".[] | select(.name == \"$CLUSTER_NAME\") | .uuid")

echo "Cluster name: $CLUSTER_NAME"
echo "Cluster UUID: $CLUSTER_UUID"
echo

DEPARTMENT_NAME="default"
DESIRED_GPU_QUOTA=0 # integer, not string
DEPARTMENT_ID=$(curl -s "$RUNAI_CTRL_PLANE/api/v1/org-unit/departments" \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H "authorization: Bearer $RUNAI_TOKEN" | jq -r ".departments[] | select(.name == \"$DEPARTMENT_NAME\" and .clusterId == \"$CLUSTER_UUID\") | .id")

echo "Department name: $DEPARTMENT_NAME"
echo "Department ID: $DEPARTMENT_ID"
echo

DEPARTMENT_SETTINGS_CURRENT=$(curl -s "$RUNAI_CTRL_PLANE/api/v1/org-unit/departments/$DEPARTMENT_ID" \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H "authorization: Bearer $RUNAI_TOKEN" | jq)

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
  -H "authorization: Bearer $RUNAI_TOKEN" \
  -H 'content-type: application/json' \
  --data-raw "[{\"nodePool\": {\"id\": \"$NODEPOOL_ID\"}, \"gpu\": {\"deserved\": $DESIRED_GPU_QUOTA}}]" | jq
# succesful change will output the new department settings with the new value set in "nodePool.gpu.deseverd"