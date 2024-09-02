#!/bin/bash

if [ "$1" == "linux" ]; then
  DIST="linux"
else
  DIST="darwin"
fi
echo "Downloading binaries for $DIST"

### runai CLI ###

if kubectl get ns runai > /dev/null 2>&1; then
    RUNAI_CLUSTER_URL=$(kubectl -n runai get ingress researcher-service-ingress -o jsonpath='{.spec.rules[0].host}')
    RUNAI_CLUSTER_VERSION=$(kubectl -n runai get deploy -o wide | tail -n 1 | awk '{ print $7 }' | awk -F: '{print $2}' | tr -d '.')
    CLI_BINARY_PATH="$HOME/runai-$RUNAI_CLUSTER_VERSION"
    wget --quiet https://$RUNAI_CLUSTER_URL/cli/$DIST -O $CLI_BINARY_PATH
    chmod +x $CLI_BINARY_PATH
    alias ra=$CLI_BINARY_PATH
    r version
    echo "CLI binary saved to '$CLI_BINARY_PATH', use 'r' alias to execute"
else
    echo "Namespace 'runai' does not exist."
fi

### runai-adm CLI ###

if kubectl get ns runai-backend > /dev/null 2>&1; then
    RUNAI_CTRL_PLANE_URL=$(kubectl -n runai-backend get ingress runai-backend-ingress -o jsonpath='{.spec.rules[0].host}')
    RUNAI_CTRL_PLANE_VERSION=$(kubectl -n runai-backend get deploy -o wide | tail -n 1 | awk '{ print $7 }' | awk -F: '{print $2}' | tr -d '.')
    ADMIN_CLI_BINARY_PATH="$HOME/runai-adm-$RUNAI_CTRL_PLANE_VERSION"
    wget --quiet https://$RUNAI_CTRL_PLANE_URL/v1/k8s/admin-cli/$DIST -O $ADMIN_CLI_BINARY_PATH
    chmod +x $ADMIN_CLI_BINARY_PATH
    alias ra=$ADMIN_CLI_BINARY_PATH
    ra version
    echo "admin CLI binary saved to '$ADMIN_CLI_BINARY_PATH', use 'ra' alias to execute"
else
    echo "Namespace 'runai-backend' does not exist."
fi
