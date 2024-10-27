#!/bin/bash

# set variables and functions

DEBUG=false  # Default is off

# Check if the script was called with the --debug flag
if [ "$1" == "--debug" ]; then
  DEBUG=true
  shift  # Remove --debug from arguments
fi

# Debugging helper function
debug() {
  if [ "$DEBUG" = true ]; then
    echo "DEBUG => $1"
  fi
}

# Check if exactly 5 parameters are provided
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
client_id="runai-admin-ui" # fixed for runai default client, can be changed: auth/admin/master/console/#/$KEYCLOAK_REALM/clients

# Printing the variables
debug "### Input values:"
debug "Username: $username"
debug "Password: $password"
debug "Control Plane URL: $CTRL_PLANE_URL"
debug "Keycloak URL: $KEYCLOAK_URL"
debug "Keycloak realm: $KEYCLOAK_REALM"
debug "Keycloak client ID: $client_id"
echo

# encoding vars
REDIRECT_URI_DECODED="$CTRL_PLANE_URL/login/callback"
ISS_DECODED="$KEYCLOAK_URL/auth/realms/$KEYCLOAK_REALM"
username_encoded=$(urlencode $username)
password_encoded=$(urlencode $password)
redirect_uri_encoded=$(urlencode $REDIRECT_URI_DECODED)
iss_encoded=$(urlencode $ISS_DECODED)

debug "### Generated URL-encoded values:"
debug "Username: $username_encoded"
debug "Password: $password_encoded"
debug "redirect URI: $redirect_uri_encoded"
debug "iss: $iss_encoded"
echo

# get login page
echo "### Step 1: get login page"
echo
login_page_url="$KEYCLOAK_URL/auth/realms/$KEYCLOAK_REALM/protocol/openid-connect/auth?response_type=code&connection=$KEYCLOAK_REALM&client_id=$client_id&redirect_uri=$redirect_uri_encoded&scope=openid+email+profile+offline_access"
response=$(curl -s -i $login_page_url)

AUTH_SESSION_ID=$(echo "$response" | grep "AUTH_SESSION_ID=" | awk -F'AUTH_SESSION_ID=' '{print substr($2, 1, 53)}')
AUTH_SESSION_ID_LEGACY=$(echo "$response" | grep "AUTH_SESSION_ID_LEGACY=" | awk -F'AUTH_SESSION_ID_LEGACY=' '{print substr($2, 1, 53)}')
KC_RESTART=$(echo "$response" | grep "KC_RESTART=" | awk -F'KC_RESTART=' '{print substr($2, 1, 991)}')
debug "### login page url: ${login_page_url}"
debug "### Response cookies:"
debug "AUTH_SESSION_ID: ${AUTH_SESSION_ID}"
debug "AUTH_SESSION_ID_LEGACY: ${AUTH_SESSION_ID_LEGACY}"
debug "KC_RESTART: ${KC_RESTART}"
echo

session_code=$(echo $response | grep "login-actions/authenticate" | awk -F'session_code=' '{print substr($2, 1, 43)}')
execution=$(echo $response | grep "login-actions/authenticate" | awk -F'execution=' '{print substr($2, 1, 36)}')
tab_id=$(echo $response | grep "login-actions/authenticate" | awk -F'tab_id=' '{print substr($2, 1, 11)}')

debug "### Response URL params:"
debug "session_code: ${session_code}"
debug "execution: ${execution}"
debug "tab_id: ${tab_id}"
echo

# perform login
echo "### Step 2: perform login"
echo

perform_login_url="$KEYCLOAK_URL/auth/realms/$KEYCLOAK_REALM/login-actions/authenticate?session_code=$session_code&execution=$execution&client_id=$client_id&tab_id=$tab_id"
login_response=$(curl -v $perform_login_url \
  -H "content-type: application/x-www-form-urlencoded" \
  -H "cookie: AUTH_SESSION_ID=$AUTH_SESSION_ID; AUTH_SESSION_ID_LEGACY=$AUTH_SESSION_ID_LEGACY; KC_RESTART=$KC_RESTART" \
  --data-raw "username=$username_encoded&password=$password_encoded&credentialId=" 2>&1)

session_state=$(echo -e $login_response | grep "location: " | awk -F'session_state=' '{print substr($2, 1, 36)}')
code=$(echo -e $login_response | grep "location: " | awk -F'&code=' '{print substr($2, 1, 110)}')

debug "### Response URL params:"
debug "session_state: ${session_state}"
debug "code: ${code}"
debug "url: ${perform_login_url}" # temp
debug "response content: ${login_response}" # temp
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
temp_token_file_path="/tmp/runai_temp_token"
echo "### the idToken: $id_token"
echo
echo $id_token > $temp_token_file_path
echo "### token written to file: $temp_token_file_path"
cat $temp_token_file_path
echo

# show decoded token
IFS='.' read -r header payload signature <<< "$id_token"

# Decode the header (Base64 URL)
decoded_header=$(echo "$header" | base64 --decode 2>/dev/null | jq .)

# Decode the payload (Base64 URL)
decoded_payload=$(echo "$payload" | base64 --decode 2>/dev/null | jq .)

# Print the decoded results
debug "Decoded Header:"
debug "$decoded_header"
echo
debug "Decoded Payload:"
debug "$decoded_payload"
echo

echo "### Step 4: test token"
echo
curl -s "$CTRL_PLANE_URL/v1/k8s/auth/me" \
  -H "authorization: Bearer $id_token" \
  -H 'content-type: application/json' | jq