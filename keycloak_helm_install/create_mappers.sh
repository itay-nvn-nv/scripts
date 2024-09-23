#!/bin/bash

# Variables
KEYCLOAK_URL="https://your-keycloak-domain.com"
REALM="your-realm"
CLIENT_ID="your-client-id"
ADMIN_USER="admin-username"
ADMIN_PASS="admin-password"
CLIENT_SCOPE_NAME="client-dedicated"
MAPPER_NAME="UID"
TOKEN_CLAIM_NAME="UID"
CLAIM_VALUE="123"
CLAIM_JSON_TYPE="String"

# Get access token
ACCESS_TOKEN=$(curl -s \
  -d "client_id=admin-cli" \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASS" \
  -d "grant_type=password" \
  "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" | jq -r '.access_token')

# Get the client scope ID
CLIENT_SCOPE_ID=$(curl -s \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$KEYCLOAK_URL/admin/realms/$REALM/client-scopes" | \
  jq -r ".[] | select(.name == \"$CLIENT_SCOPE_NAME\") | .id")

if [[ -z "$CLIENT_SCOPE_ID" ]]; then
  echo "Client scope not found!"
  exit 1
fi

# Create the mapper
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "'"$MAPPER_NAME"'",
    "protocol": "openid-connect",
    "protocolMapper": "oidc-hardcoded-claim-mapper",
    "config": {
      "claim.name": "'"$TOKEN_CLAIM_NAME"'",
      "claim.value": "'"$CLAIM_VALUE"'",
      "jsonType.label": "'"$CLAIM_JSON_TYPE"'"
    }
  }' \
  "$KEYCLOAK_URL/admin/realms/$REALM/client-scopes/$CLIENT_SCOPE_ID/protocol-mappers/models"

echo "Mapper $MAPPER_NAME added to client scope $CLIENT_SCOPE_NAME."
