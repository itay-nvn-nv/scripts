#!/bin/bash

# Check if a filename was provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide a filename as an argument."
    echo "Usage: $0 <filename>"
    exit 1
fi

ORIGINAL="$1"
COPY="${ORIGINAL}_RUNAI_USER"

# Check if the original file exists
if [ ! -f "$ORIGINAL" ]; then
    echo "Error: File '$ORIGINAL' does not exist."
    exit 1
fi

# Create a copy of the original file
cp "$ORIGINAL" "$COPY"

# Find the line containing "users" and delete from there to the end of the file
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS (BSD) sed
    sed -i '' '/users/,$d' "$COPY"
else
    # GNU sed
    sed -i '/users/,$d' "$COPY"
fi

# Append the new text to the file
cat << EOF >> "$COPY"
users:
- name: admin
  user:
    auth-provider:
      config:
        airgapped: "true"
        auth-flow: remote-browser
        realm: envinaclick
        client-id: runai-cli
        idp-issuer-url: https://app.run.ai/auth/realms/envinaclick
        redirect-uri: https://envinaclick.run.ai/oauth-code
      name: oidc
EOF

echo "Operations completed. Check '$COPY' for the result."