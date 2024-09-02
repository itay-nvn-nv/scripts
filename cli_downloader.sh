### runai CLI ###

if kubectl get ns runai > /dev/null 2>&1; then
    RUNAI_CLUSTER_URL=$(kubectl -n runai get ingress researcher-service-ingress -o jsonpath='{.spec.rules[0].host}')
    RUNAI_CLUSTER_VERSION=$(kubectl -n runai get deploy -o wide | tail -n 1 | awk '{ print $7 }' | awk -F: '{print $2}' | tr -d '.')
    CLI_BINARY_NAME="runai-$RUNAI_CLUSTER_VERSION"
    wget --content-disposition https://$RUNAI_CLUSTER_URL/cli/darwin -O $CLI_BINARY_NAME
    chmod +x $CLI_BINARY_NAME
    alias r="./$CLI_BINARY_NAME"
    r version
    echo "CLI binary saved to '$(realpath $CLI_BINARY_NAME)', use 'r' alias to execute"
else
    echo "Namespace 'runai' does not exist."
fi

### runai-adm CLI ###

if kubectl get ns runai-backend > /dev/null 2>&1; then
    RUNAI_CTRL_PLANE_URL=$(kubectl -n runai-backend get ingress runai-backend-ingress -o jsonpath='{.spec.rules[0].host}')
    RUNAI_CTRL_PLANE_VERSION=$(kubectl -n runai-backend get deploy -o wide | tail -n 1 | awk '{ print $7 }' | awk -F: '{print $2}' | tr -d '.')
    ADMIN_CLI_BINARY_NAME="runai-adm-$RUNAI_CTRL_PLANE_VERSION"
    wget --content-disposition https://$RUNAI_CTRL_PLANE_URL/v1/k8s/admin-cli/darwin -O $ADMIN_CLI_BINARY_NAME
    chmod +x $ADMIN_CLI_BINARY_NAME
    alias ra="./$ADMIN_CLI_BINARY_NAME"
    ra version
    echo "admin CLI binary saved to '$(realpath $ADMIN_CLI_BINARY_NAME)', use 'ra' alias to execute"
else
    echo "Namespace 'runai-backend' does not exist."
fi
