#!/bin/bash
# Create a Run:ai project (2.26) under the "default" department and "default" node pool.
# Admin token is auto-retrieved from the runai-backend namespace of the local kubectl context.
#
# Usage: ./create-runai-project.sh [project-name] [gpu-quota]
set -euo pipefail

PROJECT_NAME="${1:-${PROJECT_NAME:-test}}"
GPU_QUOTA="${2:-${GPU_QUOTA:-4}}"
DEPARTMENT_ID="${DEPARTMENT_ID:-4500000}"   # "default" department
NODE_POOL_ID="${NODE_POOL_ID:-100000}"      # "default" node pool
NODE_POOL_NAME="${NODE_POOL_NAME:-default}"

for cmd in kubectl curl jq; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Error: '$cmd' is required but not installed" >&2; exit 1; }
done

# Lab control planes can be flaky; retry transient failures instead of aborting.
CURL_OPTS=(--silent --show-error --max-time 60 --retry 3 --retry-delay 2 --retry-connrefused)

# ---------------------------------------------------------------------------
# 1. Retrieve admin credentials and control-plane URL from the cluster
# ---------------------------------------------------------------------------
RUNAI_ADMIN_USERNAME=$(kubectl get configmap runai-backend-tenants-manager -n runai-backend -o jsonpath='{.data.ADMIN_USERNAME}' 2>/dev/null)
RUNAI_CTRL_PLANE_URL=$(kubectl get configmap runai-backend-tenants-manager -n runai-backend -o jsonpath='{.data.TENANT_DOMAIN_TEMPLATE}' 2>/dev/null)

# ADMIN_PASSWORD lives in the tenants-manager secret unless the install points
# tenantsManager.config.existingSecret elsewhere (e.g. runai-backend-credentials),
# so find whichever secret in the namespace actually carries the key.
ADMIN_SECRET=$(kubectl get secrets -n runai-backend -o json 2>/dev/null \
  | jq -r '[.items[] | select(.data.ADMIN_PASSWORD != null) | .metadata.name]
           | (map(select(. == "runai-backend-tenants-manager")) + .) | first // empty')
if [ -n "$ADMIN_SECRET" ]; then
  RUNAI_ADMIN_PASSWORD=$(kubectl get secret "$ADMIN_SECRET" -n runai-backend -o jsonpath='{.data.ADMIN_PASSWORD}' 2>/dev/null | base64 -d)
else
  RUNAI_ADMIN_PASSWORD=""
fi

[ -z "$RUNAI_ADMIN_USERNAME" ] && echo "Error: Failed to retrieve ADMIN_USERNAME" >&2 && exit 1
[ -z "$RUNAI_ADMIN_PASSWORD" ] && echo "Error: Failed to retrieve ADMIN_PASSWORD from any secret in runai-backend" >&2 && exit 1
[ -z "$RUNAI_CTRL_PLANE_URL" ] && echo "Error: Failed to retrieve TENANT_DOMAIN_TEMPLATE" >&2 && exit 1

echo "Control plane: $RUNAI_CTRL_PLANE_URL"
echo "Admin user:    $RUNAI_ADMIN_USERNAME (password from secret/$ADMIN_SECRET)"

# ---------------------------------------------------------------------------
# 2. Exchange the admin credentials for an access token
# ---------------------------------------------------------------------------
API_RESPONSE=$(curl "${CURL_OPTS[@]}" -X POST "$RUNAI_CTRL_PLANE_URL/api/v1/token" \
  --header 'Accept: */*' \
  --header 'Content-Type: application/json' \
  --data-raw "{\"grantType\": \"password\", \"clientID\": \"cli\", \"username\": \"$RUNAI_ADMIN_USERNAME\", \"password\": \"$RUNAI_ADMIN_PASSWORD\"}")

RUNAI_TOKEN=$(echo "$API_RESPONSE" | jq -r '.accessToken // empty' 2>/dev/null)
ERROR_MESSAGE=$(echo "$API_RESPONSE" | jq -r '.message // empty' 2>/dev/null)
ERROR_CODE=$(echo "$API_RESPONSE" | jq -r '.code // empty' 2>/dev/null)

if [ -z "$RUNAI_TOKEN" ]; then
  echo "Error: Failed to retrieve API token" >&2
  [ -n "$ERROR_CODE" ] && echo "Error Code: $ERROR_CODE" >&2
  [ -n "$ERROR_MESSAGE" ] && echo "Error Message: $ERROR_MESSAGE" >&2
  [ -z "$ERROR_MESSAGE" ] && echo "API Response: $API_RESPONSE" >&2
  exit 1
fi

echo "Token retrieved."

# ---------------------------------------------------------------------------
# 3. Resolve the single cluster's UUID
# ---------------------------------------------------------------------------
CLUSTERS=$(curl "${CURL_OPTS[@]}" "$RUNAI_CTRL_PLANE_URL/api/v1/clusters" \
  --header "Authorization: Bearer $RUNAI_TOKEN" \
  --header 'Accept: application/json')

CLUSTER_COUNT=$(echo "$CLUSTERS" | jq -r 'if type == "array" then length else 0 end')
if [ "$CLUSTER_COUNT" -eq 0 ]; then
  echo "Error: No clusters returned" >&2
  echo "API Response: $CLUSTERS" >&2
  exit 1
fi
if [ "$CLUSTER_COUNT" -gt 1 ]; then
  echo "Warning: $CLUSTER_COUNT clusters found, using the first one" >&2
fi

CLUSTER_ID=$(echo "$CLUSTERS" | jq -r '.[0].uuid')
CLUSTER_NAME=$(echo "$CLUSTERS" | jq -r '.[0].name')
echo "Cluster:       $CLUSTER_NAME ($CLUSTER_ID)"

# ---------------------------------------------------------------------------
# 4. Create the project
# ---------------------------------------------------------------------------
PAYLOAD=$(jq -n \
  --arg name "$PROJECT_NAME" \
  --arg clusterId "$CLUSTER_ID" \
  --arg parentId "$DEPARTMENT_ID" \
  --arg nodePoolId "$NODE_POOL_ID" \
  --arg nodePoolName "$NODE_POOL_NAME" \
  --argjson gpu "$GPU_QUOTA" \
  '{
    name: $name,
    clusterId: $clusterId,
    parentId: $parentId,
    description: "",
    requestedNamespace: "",
    enforceRunaiScheduler: true,
    nodeTypes: {},
    resources: [
      {
        nodePool: { id: $nodePoolId, name: $nodePoolName },
        gpu: { deserved: $gpu, overQuotaWeight: $gpu },
        rank: "MediumLow"
      }
    ]
  }')

echo "Creating project '$PROJECT_NAME' with $GPU_QUOTA GPU quota..."
HTTP_BODY=$(mktemp)
HTTP_CODE=$(curl "${CURL_OPTS[@]}" -o "$HTTP_BODY" -w '%{http_code}' -X POST "$RUNAI_CTRL_PLANE_URL/api/v1/org-unit/projects" \
  --header "Authorization: Bearer $RUNAI_TOKEN" \
  --header 'Content-Type: application/json' \
  --header 'Accept: application/json' \
  --data-raw "$PAYLOAD")

if [ "$HTTP_CODE" != "201" ]; then
  echo "Error: Project creation failed (HTTP $HTTP_CODE)" >&2
  jq . "$HTTP_BODY" 2>/dev/null || cat "$HTTP_BODY" >&2
  rm -f "$HTTP_BODY"
  exit 1
fi

jq . "$HTTP_BODY"
rm -f "$HTTP_BODY"

echo "Project '$PROJECT_NAME' created."
