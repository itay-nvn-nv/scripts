#!/bin/bash

# list of vars to check
env_vars=(
    "CONTROL_PLANE_URL"
    "KEYCLOAK_ADMIN"
    "KEYCLOAK_ADMIN_PASSWORD"
    "KEYCLOAK_URL"
    "KEYCLOAK_REALM"
    "KEYCLOAK_CLIENT"
    "USER_FIRST_NAME"
    "USER_LAST_NAME"
    "USER_EMAIL"
    "USER_USERNAME"
    "USER_PASSWORD"
)

# Check if any var is empty
echo "##### Checking data:"
for var in "${env_vars[@]}"; do
  if [ -n "${!var}" ]; then
    echo "=> $var = '${!var}'"
  else
    echo "##### ERROR: $var is empty, exiting.."
    exit 1
  fi
done

APP_REDIRECT_URI="$CONTROL_PLANE_URL/oauth2/callback"
KIBANA_REDIRECT_URI="$CONTROL_PLANE_URL/oauth2/callback"
WEB_ORIGINS="$CONTROL_PLANE_URL/*"

# Get new admin access token function
get_access_token() {
  ACCESS_TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$KEYCLOAK_ADMIN" \
    -d "password=$KEYCLOAK_ADMIN_PASSWORD" \
    -d 'grant_type=password' \
    -d 'KEYCLOAK_CLIENT=admin-cli' | jq -r '.access_token')
  echo $ACCESS_TOKEN
}

# Create a new realm 
NEW_TOKEN=$(get_access_token)
curl -s -X POST "$KEYCLOAK_URL/admin/realms" \
    -H "Authorization: Bearer $NEW_TOKEN" \
    -H "Content-Type: application/json" \
    --data-raw "{
    \"realm\": \"$KEYCLOAK_REALM\",
    \"enabled\": true}"
echo "##### realm created"

# Create a new user
NEW_TOKEN=$(get_access_token)
curl -s -X POST "$KEYCLOAK_URL/admin/realms/$KEYCLOAK_REALM/users" \
-H "Authorization: Bearer $NEW_TOKEN" \
-H "Content-Type: application/json" --data-raw "{
    \"firstName\":\"$USER_FIRST_NAME\",
    \"lastName\":\"$USER_LAST_NAME\",
    \"email\":\"$USER_EMAIL\",
    \"username\":\"$USER_USERNAME\",
    \"enabled\":\"true\",
    \"emailVerified\": true,
    \"credentials\": [{\"type\": \"password\", \"value\": \"$USER_PASSWORD\", \"temporary\": false}]}"
echo "##### example user created"

# Create an OIDC client
NEW_TOKEN=$(get_access_token)
curl --location --request POST "$KEYCLOAK_URL/admin/realms/$KEYCLOAK_REALM/clients" \
--header "Authorization: Bearer $NEW_TOKEN" \
--header 'Content-Type: application/json' \
--data-raw "{
    \"clientId\": \"$KEYCLOAK_CLIENT\",
    \"redirectUris\": [\"$APP_REDIRECT_URI\",\"$KIBANA_REDIRECT_URI\"],
    \"webOrigins\": [\"$WEB_ORIGINS\"],
    \"standardFlowEnabled\": true
}"
echo "##### OIDC client created"

# Get OIDC client UUID
NEW_TOKEN=$(get_access_token)
CLIENT_UUID=$(curl --location --request GET "$KEYCLOAK_URL/admin/realms/$KEYCLOAK_REALM/clients" \
--header "Authorization: Bearer $NEW_TOKEN" \
| jq -r ".[] | select(.clientId==\"$KEYCLOAK_CLIENT\") | .id")
echo "##### OIDC client UUID retrieved"

# Enable authentication and retrieve client secret
NEW_TOKEN=$(get_access_token)
CLIENT_SECRET=$(curl --location --request GET "$KEYCLOAK_URL/admin/realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID/client-secret" \
--header "Authorization: Bearer $NEW_TOKEN" \
| jq -r ".value")
echo "##### client secret retrieved"

echo "=> CLIENT_UUID = '$CLIENT_UUID'"
echo "=> CLIENT_SECRET = '$CLIENT_SECRET'"
echo "##### post install script finished :)"