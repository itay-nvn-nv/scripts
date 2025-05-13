#!/bin/bash

# usage:
# bash log_saver.sh mycoolnamespace
# output:
# ./mycoolnamespace-logs/

NAMESPACE=$1
LOG_DIR="./$NAMESPACE-logs"
mkdir $LOG_DIR

echo "saving logs for namespace '$NAMESPACE':"

PODS=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}')

for POD in $PODS; do
  CONTAINERS=$(kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.spec.containers[*].name}')
  
  for CONTAINER in $CONTAINERS; do
    LOG_FILE="$LOG_DIR/${POD}_${CONTAINER}.log"
    
    echo "Collecting logs for Pod: $POD, Container: $CONTAINER"
    kubectl logs --timestamps $POD -c $CONTAINER -n $NAMESPACE > "$LOG_FILE"
  done
done

echo "Logs saved to $LOG_DIR"

