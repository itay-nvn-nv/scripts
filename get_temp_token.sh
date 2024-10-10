#!/bin/bash

# set variables and functions

# Check if exactly 4 parameters are provided
if [ "$#" -ne 5 ]; then
  echo "Usage: $0 <username> <password> <CTRL_PLANE_URL> <KEYCLOAK_URL> <KEYCLOAK_REALM>"
  exit 1
fi

urlencode() {
    local string="$1"
    local encoded=""
    local pos c

    for (( pos=0 ; pos<${#string} ; pos++ )); do
        c="${string:$pos:1}"
        case "$c" in
            [a-zA-Z0-9.~_-]) encoded+="$c" ;;
            *) encoded+=$(printf '%%%02X' "'$c") ;;
        esac
    done
    echo "$encoded"
}

# Assigning parameters to variables
username=$1
password=$2
CTRL_PLANE_URL=$3
KEYCLOAK_URL=$4
KEYCLOAK_REALM=$5

# Printing the variables
echo "### Input values:"
echo "Username: $username"
echo "Password: $password"
echo "Control Plane URL: $CTRL_PLANE_URL"
echo "Keycloak URL: $KEYCLOAK_URL"
echo "Keycloak realm: $KEYCLOAK_REALM"
echo

# encoding vars
REDIRECT_URI_DECODED="$CTRL_PLANE_URL/login/callback"
ISS_DECODED="$KEYCLOAK_URL/auth/realms/$KEYCLOAK_REALM"
username_encoded=$(urlencode $username)
password_encoded=$(urlencode $password)
redirect_uri_encoded=$(urlencode $REDIRECT_URI_DECODED)
iss_encoded=$(urlencode $ISS_DECODED)

echo "### Generated URL-encoded values:"
echo "Username: $username_encoded"
echo "Password: $password_encoded"
echo "redirect URI: $redirect_uri_encoded"
echo "iss: $iss_encoded"
echo

# get login page
echo "### Step 1: get login page"
echo
response=$(curl -s -i curl "$KEYCLOAK_URL/auth/realms/$KEYCLOAK_REALM/protocol/openid-connect/auth?response_type=code&connection=$KEYCLOAK_REALM&client_id=runai-admin-ui&redirect_uri=$redirect_uri_encoded&scope=openid+email+profile+offline_access")

AUTH_SESSION_ID=$(echo "$response" | grep "AUTH_SESSION_ID=" | awk -F'AUTH_SESSION_ID=' '{print substr($2, 1, 53)}')
AUTH_SESSION_ID_LEGACY=$(echo "$response" | grep "AUTH_SESSION_ID_LEGACY=" | awk -F'AUTH_SESSION_ID_LEGACY=' '{print substr($2, 1, 53)}')
KC_RESTART=$(echo "$response" | grep "KC_RESTART=" | awk -F'KC_RESTART=' '{print substr($2, 1, 991)}')

echo "### Response cookies:"
echo "AUTH_SESSION_ID: ${AUTH_SESSION_ID}"
echo "AUTH_SESSION_ID_LEGACY: ${AUTH_SESSION_ID_LEGACY}"
echo "KC_RESTART: ${KC_RESTART}"
echo

session_code=$(echo $response | grep "login-actions/authenticate" | awk -F'session_code=' '{print substr($2, 1, 43)}')
execution=$(echo $response | grep "login-actions/authenticate" | awk -F'execution=' '{print substr($2, 1, 36)}')
tab_id=$(echo $response | grep "login-actions/authenticate" | awk -F'tab_id=' '{print substr($2, 1, 11)}')

echo "### Response URL params:"
echo "session_code: ${session_code}"
echo "execution: ${execution}"
echo "tab_id: ${tab_id}"
echo

# perform login
echo "### Step 2: perform login"
echo

login_response=$(curl -v "$KEYCLOAK_URL/auth/realms/$KEYCLOAK_REALM/login-actions/authenticate?session_code=$session_code&execution=$execution&client_id=runai-admin-ui&tab_id=$tab_id" \
  -H "content-type: application/x-www-form-urlencoded" \
  -H "cookie: AUTH_SESSION_ID=$AUTH_SESSION_ID; AUTH_SESSION_ID_LEGACY=$AUTH_SESSION_ID_LEGACY; KC_RESTART=$KC_RESTART" \
  --data-raw "username=$username_encoded&password=$password_encoded&credentialId=" 2>&1)

session_state=$(echo -e $login_response | grep "location: " | awk -F'session_state=' '{print substr($2, 1, 36)}')
code=$(echo -e $login_response | grep "location: " | awk -F'&code=' '{print substr($2, 1, 110)}')

echo "### Response URL params:"
echo "session_state: ${session_state}"
echo "code: ${code}"
echo

# get token
echo "### Step 3: get token"
echo

token_response=$(curl -s "$CTRL_PLANE_URL/api/v1/token" \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H 'authorization: Bearer' \
  -H 'content-type: application/json' \
  -H "origin: $CTRL_PLANE_URL" \
  -H 'priority: u=1, i' \
  -H "referer: $CTRL_PLANE_URL/login/callback?session_state=$session_state&iss=$iss_encoded&code=$code" \
  --data-raw "{\"grantType\":\"exchange_token\",\"code\":\"$code\",\"redirectUri\":\"$CTRL_PLANE_URL/login/callback\"}")

id_token=$(echo $token_response | jq -r '.idToken')
echo "### the idToken: $id_token"
echo

echo "### Step 4: test token"
echo
curl -s "$CTRL_PLANE_URL/v1/k8s/auth/me" \
  -H "authorization: Bearer $id_token" \
  -H 'content-type: application/json' | jq