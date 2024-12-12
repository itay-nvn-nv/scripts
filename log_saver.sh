#!/bin/bash

# Set the namespace to collect logs from
NAMESPACE="runai-backend"

# Create a directory to store logs
LOG_DIR=$(pwd)

# Get the list of all pods in the namespace
PODS=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}')

# Loop through each pod
for POD in $PODS; do
  # Get containers in the pod
  CONTAINERS=$(kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.spec.containers[*].name}')
  
  for CONTAINER in $CONTAINERS; do
    # Save logs to a file named after the pod and container
    LOG_FILE="$LOG_DIR/${POD}_${CONTAINER}.log"
    
    # Collect logs
    echo "Collecting logs for Pod: $POD, Container: $CONTAINER"
    kubectl logs --timestamps $POD -c $CONTAINER -n $NAMESPACE > "$LOG_FILE"
  done
done

echo "Logs saved to $LOG_DIR"

