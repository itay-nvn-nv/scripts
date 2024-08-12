#!/bin/bash

source config.env

# list of vars to check
env_vars=(
    "WEB_APP_URL"
    "KEYCLOAK_ADMIN"
    "KEYCLOAK_ADMIN_PASSWORD"
    "KEYCLOAK_URL"
    "KEYCLOAK_REALM"
    "KEYCLOAK_CLIENT_ID"
    "KEYCLOAK_CLIENT_TYPE"
    "USER_FIRST_NAME"
    "USER_LAST_NAME"
    "USER_EMAIL"
    "USER_USERNAME"
    "USER_PASSWORD"
)

# Check vars are populated
echo "##### Checking config.env:"
for var in "${env_vars[@]}"; do
  if [ -n "${!var}" ]; then
    echo "=> '$var' is set to '${!var}'"
  else
    echo "##### ERROR: $var is empty, exiting.."
    exit 1
  fi
done

# Get an admin-scoped access token
get_access_token() {
  ACCESS_TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$KEYCLOAK_ADMIN" \
    -d "password=$KEYCLOAK_ADMIN_PASSWORD" \
    -d 'grant_type=password' \
    -d 'KEYCLOAK_CLIENT=admin-cli' | jq -r '.access_token')
  echo $ACCESS_TOKEN
}

# Create realm
create_realm() {
  curl -s -X POST "$KEYCLOAK_URL/admin/realms" \
      -H "Authorization: Bearer $NEW_TOKEN" \
      -H "Content-Type: application/json" \
      --data-raw "{
      \"realm\": \"$KEYCLOAK_REALM\",
      \"enabled\": true}"
  echo "##### realm '$KEYCLOAK_REALM' created"
}

# Create user
create_user() {
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
echo "##### example user '$USER_EMAIL' created"
}

# Create an OIDC client
create_oidc_client() {
  echo "##### Creating OIDC client '$KEYCLOAK_CLIENT_ID'..."
  curl --location -s -X POST "$KEYCLOAK_URL/admin/realms/$KEYCLOAK_REALM/clients" \
  --header "Authorization: Bearer $NEW_TOKEN" \
  --header 'Content-Type: application/json' \
  --data-raw "{
      \"clientId\": \"$KEYCLOAK_CLIENT_ID\",
      \"redirectUris\": [\"$WEB_APP_URL/auth/realms/runai/broker/oidc/endpoint\"],
      \"webOrigins\": [\"$WEB_APP_URL/*\"],
      \"attributes\": {
        \"login_theme\": \"genny\",
        \"post.logout.redirect.uris\": \"$WEB_APP_URL/*\"},
      \"standardFlowEnabled\": true
  }"
  echo "##### OIDC client '$KEYCLOAK_CLIENT_ID' created"
  CLIENT_UUID=$(curl --location -s -X GET "$KEYCLOAK_URL/admin/realms/$KEYCLOAK_REALM/clients" \
  --header "Authorization: Bearer $NEW_TOKEN" \
  | jq -r ".[] | select(.clientId==\"$KEYCLOAK_CLIENT_ID\") | .id")
  echo "=> OIDC client UUID: '$CLIENT_UUID'"
  CLIENT_SECRET=$(curl --location -s -X GET "$KEYCLOAK_URL/admin/realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID/client-secret" \
  --header "Authorization: Bearer $NEW_TOKEN" \
  | jq -r ".value")
  echo "##### client credentials retrieved"
  echo "=> OIDC client secret: '$CLIENT_SECRET'"
}

# Create a SAML client
create_saml_client() {
  echo "##### Creating SAML client '$KEYCLOAK_CLIENT_ID'..."
  curl --location -s -X POST "$KEYCLOAK_URL/admin/realms/$KEYCLOAK_REALM/clients" \
  --header "Authorization: Bearer $TOKEN" \
  --header "Content-Type: application/json" \
  --data-raw "{
    \"clientId\": \"$KEYCLOAK_CLIENT_ID\",
    \"protocol\": \"saml\",
    \"enabled\": true,
    \"redirectUris\": [\"$WEB_APP_URL/saml/callback\"],
    \"baseUrl\": \"$WEB_APP_URL\",
    \"attributes\": {
      \"saml.assertion.signature\": \"false\",
      \"saml.force.post.binding\": \"true\",
      \"saml.multivalued.roles\": \"false\",
      \"saml.encrypt\": \"false\",
      \"saml.server.signature\": \"false\",
      \"saml.server.signature.keyinfo.ext\": \"false\",
      \"exclude.session.state.from.auth.response\": \"false\",
      \"saml_force_name_id_format\": \"false\",
      \"saml.client.signature\": \"false\",
      \"tls.client.certificate.bound.access.tokens\": \"false\",
      \"saml.authnstatement\": \"false\",
      \"display.on.consent.screen\": \"false\",
      \"saml.onetimeuse.condition\": \"false\"
    }
  }"
  echo "##### SAML client '$KEYCLOAK_CLIENT_ID' created"
  CLIENT_UUID=$(curl --location -s -X GET "$KEYCLOAK_URL/admin/realms/$KEYCLOAK_REALM/clients" \
  --header "Authorization: Bearer $NEW_TOKEN" \
  | jq -r ".[] | select(.clientId==\"$KEYCLOAK_CLIENT_ID\") | .id")
  echo "=> SAML client UUID: '$CLIENT_UUID'"
  SAML_ENDPOINT="$KEYCLOAK_URL/realms/$KEYCLOAK_REALM/protocol/saml/descriptor"
  echo "=> SAML 2.0 endpoint URL: '$SAML_ENDPOINT'"
}

# start:
NEW_TOKEN=$(get_access_token)
create_realm
create_user

if [[ $KEYCLOAK_CLIENT_TYPE =~ ^(oidc|OIDC)$ ]]; then
    create_oidc_client
elif [[ $KEYCLOAK_CLIENT_TYPE =~ ^(saml|SAML)$ ]]; then
    create_saml_client
else
    echo "##### The client type provided '$KEYCLOAK_CLIENT_TYPE' is not valid, proceeding with OIDC by default"
    create_oidc_client
fi

echo "##### post install script finished :)"