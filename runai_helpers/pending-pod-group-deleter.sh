#!/bin/bash

# provide namespace when running script:
# namespace="test" ./pending-pod-group-deleter.sh

echo "Checking namespace '$namespace'"

# Get all IW resources
all_iws=$(kubectl get iw -n "$namespace" -o jsonpath='{.items[*].metadata.name}')

# Filter IW resources to get only those in Pending state
pending_iws=()
for iw in $all_iws; do
    status=$(kubectl get iw "$iw" -n "$namespace" -o jsonpath='{.status.phase}')
    if [ "$status" == "Pending" ]; then
        pending_iws+=("$iw")
    fi
done


# Iterate through each Pending IW resource
for iw in "${pending_iws[@]}"; do
  echo "Processing IW: $iw"

  # Grab the workload ID from the annotation
  workload_id=$(kubectl get iw "$iw" -n "$namespace" -o jsonpath='{.metadata.annotations.workloadId}')

  # Check if workload_id is empty.  If so, skip to the next IW.  Important to prevent errors.
  if [ -z "$workload_id" ]; then
    echo "Workload ID not found for IW: $iw. Skipping."
    continue
  fi

  echo "Workload ID: $workload_id"

  # Find pods with the matching top-owner-uid label
  pods=$(kubectl get pods -n "$namespace" -o jsonpath='{range .items[?(@.metadata.labels.run\.ai/top-owner-uid=="'$workload_id'")]}{.metadata.name}{"\n"}{end}')

  # Find PodGroups with the matching workloadId annotation
  pgs=$(kubectl get pg -n "$namespace" -o jsonpath='{range .items[?(@.metadata.annotations.workloadId=="'$workload_id'")]}{.metadata.name}{"\n"}{end}' 2>/dev/null || echo "")

  # Print the resources to be deleted (for verification)
  echo "Pods to be deleted:"
  echo "$pods"
  echo "PodGroups to be deleted:"
  echo "$pgs"

  # Delete the PodGroups
  if [ -n "$pgs" ]; then
    echo "Deleting PodGroups..."
    kubectl get pg -n "$namespace" $(echo "$pgs") -o yaml > ${iw}_pg_${pgs}.yaml
    kubectl delete pg -n "$namespace" $(echo "$pgs")
  else
    echo "No PodGroups found to delete."
  fi

  # Delete the pods
  if [ -n "$pods" ]; then
    echo "Deleting pods..."
    kubectl get pod -n "$namespace" $(echo "$pods") -o yaml > ${iw}_pod_${pods}.yaml
    kubectl delete pod -n "$namespace" $(echo "$pods")
  else
    echo "No pods found to delete."
  fi

  echo "Finished processing IW: $iw"
  echo "-------------------------"
done

echo "Script completed."