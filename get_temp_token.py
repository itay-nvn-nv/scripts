import sys
import requests
import json
import base64
import urllib.parse
import argparse

parser = argparse.ArgumentParser(description="Retrieve temporary OIDC token from keycloak")
parser.add_argument("--username", help="Username for authentication", type=str, required=True)
parser.add_argument("--password", help="Password for authentication", type=str, required=True)
parser.add_argument("--CTRL_PLANE_URL", help="Control Plane URL", type=str, required=True)
parser.add_argument("--KEYCLOAK_URL", help="Keycloak URL", type=str, required=True)
parser.add_argument("--KEYCLOAK_REALM", help="Keycloak realm", type=str, required=True)
parser.add_argument("--debug", action="store_true", help="Enable debug mode", default=False)

args = parser.parse_args()

DEBUG = args.debug

def debug(message):
    if DEBUG:
        print(f"DEBUG => {message}")

username=args.username
password=args.password
CTRL_PLANE_URL=args.CTRL_PLANE_URL
KEYCLOAK_URL=args.KEYCLOAK_URL
KEYCLOAK_REALM=args.KEYCLOAK_REALM
client_id = "runai-admin-ui"

debug("### Input values:")
debug(f"Username: {username}")
debug(f"Password: {password}")
debug(f"Control Plane URL: {CTRL_PLANE_URL}")
debug(f"Keycloak URL: {KEYCLOAK_URL}")
debug(f"Keycloak realm: {KEYCLOAK_REALM}")
debug(f"Keycloak client ID: {client_id}")
print()

REDIRECT_URI_DECODED = f"{CTRL_PLANE_URL}/login/callback"
ISS_DECODED = f"{KEYCLOAK_URL}/auth/realms/{KEYCLOAK_REALM}"
username_encoded = urllib.parse.quote(username, safe='')
password_encoded = urllib.parse.quote(password, safe='')
redirect_uri_encoded = urllib.parse.quote(REDIRECT_URI_DECODED, safe='')
iss_encoded = urllib.parse.quote(ISS_DECODED, safe='')

debug("### Generated URL-encoded values:")
debug(f"Username: {username_encoded}")
debug(f"Password: {password_encoded}")
debug(f"redirect URI: {redirect_uri_encoded}")
debug(f"iss: {iss_encoded}")
print()

# Step 1: get login page
def get_login_page():
    print("### Step 1: get login page")
    print()
    response = requests.get(f"{KEYCLOAK_URL}/auth/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth", 
                            params={
                                "response_type": "code",
                                "connection": KEYCLOAK_REALM,
                                "client_id": client_id,
                                "redirect_uri": redirect_uri_encoded,
                                "scope": "openid email profile offline_access"
                            })

    cookies = response.cookies
    AUTH_SESSION_ID = cookies.get('AUTH_SESSION_ID')
    AUTH_SESSION_ID_LEGACY = cookies.get('AUTH_SESSION_ID_LEGACY')
    KC_RESTART = cookies.get('KC_RESTART')

    debug("### Response cookies:")
    debug(f"AUTH_SESSION_ID: {AUTH_SESSION_ID}")
    debug(f"AUTH_SESSION_ID_LEGACY: {AUTH_SESSION_ID_LEGACY}")
    debug(f"KC_RESTART: {KC_RESTART}")
    print()
    # Extract session_code, execution, and tab_id from the response
    # This part might need adjustment based on the actual response structure
    session_code = ''
    execution = ''
    tab_id = ''
    # Add logic to extract these values from the response

    debug("### Response URL params:")
    debug(f"session_code: {session_code}")
    debug(f"execution: {execution}")
    debug(f"tab_id: {tab_id}")
    print()
    
    print(response.request.url)

    for cookie in response.cookies:
        print(f"COOKIES | {cookie.name}: {cookie.value}")

    for header, value in response.headers.items():
        print(f"HEADERS | {header}: {value}")

# Step 2: perform login
def perform_login():
    print("### Step 2: perform login")
    print()

    login_response = requests.post(
        f"{KEYCLOAK_URL}/auth/realms/{KEYCLOAK_REALM}/login-actions/authenticate",
        params={
            "session_code": session_code,
            "execution": execution,
            "client_id": client_id,
            "tab_id": tab_id
        },
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "cookie": f"AUTH_SESSION_ID={AUTH_SESSION_ID}; AUTH_SESSION_ID_LEGACY={AUTH_SESSION_ID_LEGACY}; KC_RESTART={KC_RESTART}"
        },
        data={
            "username": username_encoded,
            "password": password_encoded,
            "credentialId": ""
        },
        allow_redirects=False
    )

    location = login_response.headers.get('Location', '')
    global session_state
    global code 
    session_state = urllib.parse.parse_qs(urllib.parse.urlparse(location).query).get('session_state', [''])[0]
    code = urllib.parse.parse_qs(urllib.parse.urlparse(location).query).get('code', [''])[0]

    debug("### Response URL params:")
    debug(f"session_state: {session_state}")
    debug(f"code: {code}")
    print()

# Step 3: get token
def get_token():
    print("### Step 3: get token")
    print()

    token_response = requests.post(
        f"{CTRL_PLANE_URL}/api/v1/token",
        headers={
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': 'Bearer',
            'content-type': 'application/json',
            'origin': CTRL_PLANE_URL,
            'priority': 'u=1, i',
            'referer': f"{CTRL_PLANE_URL}/login/callback?session_state={session_state}&iss={iss_encoded}&code={code}"
        },
        json={
            "grantType": "exchange_token",
            "code": code,
            "redirectUri": f"{CTRL_PLANE_URL}/login/callback"
        }
    )

    token_data = token_response.json()
    global id_token
    id_token = token_data.get('idToken')
    print(f"### the idToken: {id_token}")
    print()

    # Show decoded token
    header, payload, signature = id_token.split('.')

    # Decode the header and payload
    decoded_header = json.loads(base64.urlsafe_b64decode(header + '==').decode('utf-8'))
    decoded_payload = json.loads(base64.urlsafe_b64decode(payload + '==').decode('utf-8'))

    debug("Decoded Header:")
    debug(json.dumps(decoded_header, indent=2))
    print()
    debug("Decoded Payload:")
    debug(json.dumps(decoded_payload, indent=2))
    print()

# Step 4: test token
def test_token():
    print("### Step 4: test token")
    print()
    test_response = requests.get(
        f"{CTRL_PLANE_URL}/v1/k8s/auth/me",
        headers={
            "authorization": f"Bearer {id_token}",
            'content-type': 'application/json'
        }
    )
    print(json.dumps(test_response.json(), indent=2))


get_login_page()
# perform_login()
# get_token()
# test_token()