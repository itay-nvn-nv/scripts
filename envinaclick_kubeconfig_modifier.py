#!/usr/bin/env python3
import yaml
import argparse
import sys
import subprocess

##### for SaaS clusters:
#
# python3 envinaclick_kubeconfig_modifier.py \
#         --input-yaml original_kuebconfig.yaml \
#
##### for self-hosted clusters:
#
# python3 envinaclick_kubeconfig_modifier.py \
#         --input-yaml original_kuebconfig.yaml \
#         --ctrl-plane-url https://blabla.runailabs-cs.com \
#         --self-hosted

parser = argparse.ArgumentParser(description="Env-In-A-Click kubeconfig file modify script", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--self-hosted", action="store_true", default=False, help="Set cluster as self hosted")
parser.add_argument("--input-yaml", dest="input_yaml", type=str, required=True, help="Set the input file path")
parser.add_argument("--ctrl-plane-url", dest="ctrl_plane_url", default="https://envinaclick.run.ai", type=str, help="ctrl plane URL")
parser.add_argument("--keycloak-realm", dest="keycloak_realm", default="envinaclick", type=str, help="keycloak realm")
args = parser.parse_args()

if args.self_hosted and not args.ctrl_plane_url:
    print("Error: '--ctrl-plane-url' must be provided if '--self-hosted' is set.")
    sys.exit(1)

CTRL_PLANE_URL = args.ctrl_plane_url
REALM= args.keycloak_realm
IDP_ISSUER_URL=f"https://app.run.ai/auth/realms/{REALM}"
REDIRECT_URI=f"{CTRL_PLANE_URL}/oauth-code"
INPUT_YAML=args.input_yaml
OUTPUT_YAML=f"{INPUT_YAML.split(".yaml")[0]}_EIAC_modified.yaml"

print(f"input kubeconfig file: {INPUT_YAML}")
print(f"writing modified file to: {OUTPUT_YAML}")

if args.self_hosted:
    REALM="runai"
    IDP_ISSUER_URL=f"{CTRL_PLANE_URL}/auth/realms/{REALM}"
    REDIRECT_URI=f"{CTRL_PLANE_URL}/oauth-code"

with open(INPUT_YAML, 'r') as file:
    data = yaml.safe_load(file)

new_user = {
  "name": "runai-user",
  "user": {
    "auth-provider": {
      "config": {
        "airgapped": "true",
        "auth-flow": "remote-browser",
        "client-id": "runai-cli",
        "idp-issuer-url": IDP_ISSUER_URL,
        "realm": REALM,
        "redirect-uri": REDIRECT_URI
      },
      "name": "oidc"
    }
  }
}

new_context = {
      "context": {
        "cluster": data['clusters'][0]['name'],
        "user": "runai-user"
      },
      "name": "runai-user"
    }

data['contexts'][0]['name'] = "cluster-admin"
data['current-context'] = "cluster-admin"
data['contexts'].append(new_context)
data['users'].append(new_user)

# Write the modified data back to YAML
with open(OUTPUT_YAML, 'w') as file:
    yaml.dump(data, file)

# Run kubectl command to get contexts
print("Testing modified file:")
try:
    result = subprocess.run(
        ["kubectl", "--kubeconfig", OUTPUT_YAML, "config", "get-contexts"],
        text=True,
        capture_output=True,
        check=True
    )
    # Print command output
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print(f"Error occurred: {e.stderr}")
