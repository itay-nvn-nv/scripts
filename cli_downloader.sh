# define details
RUNAI_URL=$(kubectl -n runai get ingress researcher-service-ingress -o jsonpath='{.spec.rules[0].host}')
RUNAI_VERSION=$(kubectl -n runai get deploy cluster-sync -o jsonpath='{.spec.template.spec.containers[?(@.name=="cluster-sync")].env[?(@.name=="CLUSTER_VERSION")].value}')
RUNAI_VERSION_CLEAN=$(echo "$RUNAI_VERSION" | tr -d '.')
CLI_BINARY_NAME="runai-$RUNAI_VERSION_CLEAN"

# download binary
wget --content-disposition https://$RUNAI_URL/cli/darwin -O $CLI_BINARY_NAME

# allow execution
chmod +x $CLI_BINARY_NAME

# create alias "r" (to keep "runai" alias free)
alias r="./$CLI_BINARY_NAME"

# check cli version
r version
