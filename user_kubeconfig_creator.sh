#!/bin/bash

# for saas:
# bash kubeconfig_modifier.sh --file /path/to/kubeconfig

# for self-hosted:
# bash kubeconfig_modifier.sh --file /path/to/kubeconfig --self-hosted https://my-control-plane-url


# Ensure yq is installed
if ! command -v yq &> /dev/null; then
    echo "yq command not found. Please install yq to run this script."
    exit 1
fi

# Usage information
usage() {
    echo "Usage: $0 --file /path/to/kubeconfig [--self-hosted CTRL_PLANE_URL]"
    exit 1
}

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --file) KUBECONFIG_FILE="$2"; shift ;;
        --self-hosted) SELF_HOSTED=true; CTRL_PLANE_URL="$2"; shift ;;
        *) usage ;;
    esac
    shift
done

# Verify kubeconfig file is provided
if [[ -z "$KUBECONFIG_FILE" ]]; then
    usage
fi

# Set default values for SaaS
REALM="envinaclick"
IDP_ISSUER_URL="https://app.run.ai/auth/realms/envinaclick"
REDIRECT_URI="https://envinaclick.run.ai/oauth-code"

# Override for self-hosted if applicable
if [[ "$SELF_HOSTED" == true ]]; then
    if [[ -z "$CTRL_PLANE_URL" ]]; then
        echo "Error: --self-hosted requires CTRL_PLANE_URL to be passed."
        exit 1
    fi
    REALM="runai-realm"
    IDP_ISSUER_URL="$CTRL_PLANE_URL/auth/realms/envinaclick"
    REDIRECT_URI="$CTRL_PLANE_URL/oauth-code"
fi

# Modify the kubeconfig file using yq
yq eval "
  .contexts += [{
    \"context\": {
      \"cluster\": \"my-cool-cluster\",
      \"user\": \"runai-user\"
    },
    \"name\": \"runai-user\"
  }]
  |
  .users += [{
    \"name\": \"runai-user\",
    \"user\": {
      \"auth-provider\": {
        \"config\": {
          \"airgapped\": \"true\",
          \"auth-flow\": \"remote-browser\",
          \"realm\": \"$REALM\",
          \"client-id\": \"runai-cli\",
          \"idp-issuer-url\": \"$IDP_ISSUER_URL\",
          \"redirect-uri\": \"$REDIRECT_URI\"
        },
        \"name\": \"oidc\"
      }
    }
  }]
  |
  .contexts[0].name = \"admin\"
" "$KUBECONFIG_FILE" > "$KUBECONFIG_FILE.modified"

echo "Kubeconfig modification complete. New file is saved as $KUBECONFIG_FILE.modified."
