#!/bin/bash

echo "Checking required utilities..."

command -v brew >/dev/null 2>&1 || { echo "Install Homebrew first: https://brew.sh"; exit 1; }

for cmd in argocd jq; do
    command -v $cmd >/dev/null 2>&1 || { echo "Installing $cmd..."; brew install $cmd; }
done

echo "All required utilities are installed!"
echo ""

echo "Checking login status to ArgoCD..."
if argocd account get-user-info --grpc-web | grep -q "Logged In: true"; then
  echo "Already logged in, moving on..."
  echo ""
  argocd account get-user-info --grpc-web
  echo ""
else
  echo "Not logged in, logging in..."
  echo ""
  argocd login argocd-infra-main-01.runailabs.com --grpc-web --sso
fi

APPS=($(argocd app list -p customer-success -o name --grpc-web))

if [ ${#APPS[@]} -eq 0 ]; then
    echo "No applications found."
    exit 1
fi

select_app() {
    echo "Select an ArgoCD application:"
    select APP in "${APPS[@]}"; do
        if [[ -n "$APP" ]]; then
            echo "You selected $APP"
            printf "\n"
            break
        else
            echo "Invalid selection. Please try again."
            printf "\n"
        fi
    done
}

get_app_info() {
    echo "$APP status:"
    eval $(argocd app get $APP -o json --grpc-web | jq -r '{
    SLEEP_STATUS: .metadata.labels["env-in-a-click/status"],
    HEALTH_STATUS: .status.health.status,
    SYNC_STATUS: .status.sync.status
    } | to_entries | map("export " + .key + "=\"" + .value + "\"") | .[]')
    echo "Sync: $SYNC_STATUS, Health: $HEALTH_STATUS, Sleep: $SLEEP_STATUS"
    echo ""
}

wake_up_app() {
    echo "Performing Wakeup operations..."
    argocd app patch $APP --type merge -p '{"metadata": {"labels": {"env-in-a-click/status": "wake-up"}}}' --grpc-web
    argocd app sync $APP --grpc-web
    echo "$APP is set to wake-up status"
    echo ""
}

hibernate_app() {
    echo "Performing Hibernate operations..."
    argocd app patch $APP --type merge -p '{"metadata": {"labels": {"env-in-a-click/status": "wake-up"}}}' --grpc-web
    argocd app sync $APP --grpc-web
    echo "$APP is set to hibernating status"
    echo ""
}

get_kubeconfig() {
    clean_app="${APP#argocd/}"
    kubeconfig_file_name="${clean_app}_kubeconfig.yaml"
    echo "Performing Get Kubeconfig operations..."
    kubeconfig_content=$(argocd app logs $APP --name kubeconfig-exposer --grpc-web)
    if echo "$kubeconfig_content" | grep -q "kind: Config"; then
        echo "Kubeconfig appears to be valid, proceeding..."
        printf "%s\n" "$kubeconfig_content" > $kubeconfig_file_name
        kubeconfig_full_path=$(realpath $kubeconfig_file_name)
        echo "kubeconfig file saved at: $kubeconfig_full_path"
        export KUBECONFIG=$kubeconfig_full_path
        echo ""
    else
        echo "Invalid or empty kubeconfig"
    fi
}

options=("Hibernate" "Wakeup" "Get Kubeconfig" "Show app status" "Change app" "Exit")

display_menu() {
    get_app_info
    echo "Select an operation for app $APP:"
    for ((i=0; i<${#options[@]}; i++)); do
        echo "$((i+1)). ${options[$i]}"
    done
}

select_app

while true; do
    display_menu
    read -rp "Enter your choice [1-${#options[@]}]: " choice
    printf "\n"
    case $choice in
        1) hibernate_app ; echo "" ;;
        2) wake_up_app ; echo "" ;;
        3) get_kubeconfig ; echo "" ;;
        4) get_app_info ; echo "" ;;
        5) select_app ; echo "" ;;
        6) echo "Exiting." ; exit 0 ;;
        *) echo "Invalid choice. Please enter a number from 1 to ${#options[@]}." ; echo "" ;;
    esac
    echo
done
