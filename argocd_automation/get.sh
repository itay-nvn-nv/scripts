#!/bin/bash

kubeconfig_file_name="$1_kubeconfig.yaml"

echo "Checking login status:"
if argocd account get-user-info --grpc-web | grep -q "Logged In: true"; then
  echo "Already logged in, moving on..."
  argocd account get-user-info --grpc-web
else
  echo "Not logged in, logging in..."
  argocd login argocd-infra-main-01.runailabs.com --grpc-web --sso
fi

echo "Checking app $1:"
while true; do
    SYNC_STATUS=$(argocd app get $1 --grpc-web | grep "Sync Status" | awk '{ print $3 }')
    HEALTH_STATUS=$(argocd app get $1 --grpc-web | grep "Health Status" | awk '{ print $3 }')
    if [ "$HEALTH_STATUS" == "Healthy" ] && [ "$SYNC_STATUS" == "Synced" ]; then
        echo "app $1 is healthy!"
        break
    else
        echo "App sync status: $SYNC_STATUS"
        echo "App health status: $HEALTH_STATUS"
        echo "Waiting for $1 app to become healthy..."
    fi
    sleep 10
done

argocd app logs $1 --name kubeconfig-exposer --grpc-web > $kubeconfig_file_name

kubeconfig_full_path=$(realpath $kubeconfig_file_name)
echo "kubeconfig file saved at: $kubeconfig_full_path"

export KUBECONFIG=$kubeconfig_full_path

kubectl get nodes -o wide
kubectl -n runai get pods
