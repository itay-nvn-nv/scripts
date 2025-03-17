#!/bin/bash

# Namespaces to check
NAMESPACES=("runai" "runai-backend")

for NAMESPACE in "${NAMESPACES[@]}"; do
  kubectl get namespace "$NAMESPACE" >/dev/null 2>&1
  if [ $? -ne 0 ]; then
    echo "Namespace '$NAMESPACE' does not exist. Skipping."
    continue
  fi

  echo "Namespace '$NAMESPACE' exists. Listing pods:"
  kubectl get pods -n "$NAMESPACE"
  LOG_DIR="./$NAMESPACE-logs"
  LOG_ARCHIVE_NAME="$NAMESPACE-logs.tar"
  mkdir $LOG_DIR
  PODS=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}')

  for POD in $PODS; do
    CONTAINERS=$(kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.spec.containers[*].name}')
    
    for CONTAINER in $CONTAINERS; do
      LOG_FILE="$LOG_DIR/${POD}_${CONTAINER}.log"
      echo "Collecting logs for Pod: $POD, Container: $CONTAINER"
      kubectl logs --timestamps $POD -c $CONTAINER -n $NAMESPACE > "$LOG_FILE"
    done
  done

  du -hs $LOG_DIR
  tar cvf $LOG_ARCHIVE_NAME $LOG_DIR
  ls -lah $LOG_ARCHIVE_NAME
  rm -rf $LOG_DIR
  echo "Logs archived to $LOG_ARCHIVE_NAME"

done