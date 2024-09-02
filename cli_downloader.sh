#!/bin/bash

if [ "$1" == "linux" ]; then
  DIST="linux"
else
  DIST="darwin"
fi
echo "Downloading binaries for $DIST"

### runai CLI ###

if kubectl get ns runai > /dev/null 2>&1; then
    RUNAI_CLUSTER_URL=$(kubectl -n runai get deploy cluster-sync -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="CLUSTER_DOMAIN")].value}')
    echo "Run:AI cluster URL: $RUNAI_CLUSTER_URL"
    RUNAI_CLUSTER_VERSION=$(kubectl -n runai get deploy -o wide | tail -n 1 | awk '{ print $7 }' | awk -F: '{print $2}')
    echo "Run:AI cluster version: $RUNAI_CLUSTER_VERSION"
    CLI_BINARY_PATH="$HOME/runai-$(echo $RUNAI_CLUSTER_VERSION | tr -d '.')"
    wget --quiet --content-disposition https://$RUNAI_CLUSTER_URL/cli/$DIST -O $CLI_BINARY_PATH
    chmod +x $CLI_BINARY_PATH
    echo "CLI binary saved to '$CLI_BINARY_PATH', assign it to the 'r' alias by running:"
    echo "alias r=$CLI_BINARY_PATH"
else
    echo "Namespace 'runai' does not exist."
fi

### runai-adm CLI ###

if kubectl get ns runai-backend > /dev/null 2>&1; then
    RUNAI_CTRL_PLANE_URL=$(kubectl -n runai-backend get configmap runai-backend-identity-manager -o jsonpath="{.data.APP_URL}")
    echo "Run:AI control plane URL: $RUNAI_CTRL_PLANE_URL"
    RUNAI_CTRL_PLANE_VERSION=$(kubectl -n runai-backend get deploy -o wide | tail -n 1 | awk '{ print $7 }' | awk -F: '{print $2}')
    echo "Run:AI control plane version: $RUNAI_CTRL_PLANE_VERSION"
    ADMIN_CLI_BINARY_PATH="$HOME/runai-adm-$(echo $RUNAI_CTRL_PLANE_VERSION | tr -d '.')"
    wget --quiet https://$RUNAI_CTRL_PLANE_URL/v1/k8s/admin-cli/$DIST -O $ADMIN_CLI_BINARY_PATH
    chmod +x $ADMIN_CLI_BINARY_PATH
    echo "admin CLI binary saved to '$ADMIN_CLI_BINARY_PATH', assign it to the 'ra' alias by running:"
    echo "alias ra=$ADMIN_CLI_BINARY_PATH"
else
    echo "Namespace 'runai-backend' does not exist."
fi
