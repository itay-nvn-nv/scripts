#!/usr/bin/env python3
import yaml
import argparse
import sys

##### for SaaS clusters:
#
# python3 envinaclick_kubeconfig_modifier.py \
#         --input-yaml original_kuebconfig.yaml \
#         --output-yaml modified_kuebconfig.yaml
#
##### for self-hosted clusters:
#
# python3 envinaclick_kubeconfig_modifier.py \
#         --input-yaml original_kuebconfig.yaml \
#         --output-yaml modified_kuebconfig.yaml \
#         --ctrl-plane-url https://blabla.runailabs-cs.com \
#         --self-hosted

def parse_arguments():
    parser = argparse.ArgumentParser(description="Env-In-A-Click kubeconfig file modify script")
    parser.add_argument("--self-hosted", action="store_true", help="Set cluster as self hosted (default is False for saas clsuters))")
    parser.add_argument("--input-yaml", dest="input_yaml", help="Set the input file path")
    parser.add_argument("--output-yaml", dest="output_yaml", help="Set the output file path")
    parser.add_argument("--ctrl-plane-url", dest="ctrl_plane_url", help="Set the ctrl plane URL")
    return parser.parse_args()

def validate_args(args):
    if args.self_hosted and not args.ctrl_plane_url:
        print("Error: '--ctrl-plane-url' must be provided if '--self-hosted' is set.")
        sys.exit(1)

args = parse_arguments()
validate_args(args)

SELF_HOSTED = args.self_hosted or False
CTRL_PLANE_URL = args.ctrl_plane_url or ""
REALM="envinaclick"
IDP_ISSUER_URL="https://app.run.ai/auth/realms/envinaclick"
REDIRECT_URI="https://envinaclick.run.ai/oauth-code"
INPUT_YAML=args.input_yaml
OUTPUT_YAML=args.output_yaml

if SELF_HOSTED:
    REALM="runai"
    IDP_ISSUER_URL=f"{CTRL_PLANE_URL}/auth/realms/envinaclick"
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
        "user": "admin"
      },
      "name": "runai-user"
    }

data['contexts'][0]['name'] = "cluster-admin"
data['current-context'] = "cluster-admin"
data['users'].append(new_context)
data['users'].append(new_user)

# Write the modified data back to YAML
with open(OUTPUT_YAML, 'w') as file:
    yaml.dump(data, file)