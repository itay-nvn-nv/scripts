#!/bin/bash

# CRD API groups to check
CRDS=("distributedpolicies.run.ai" "inferencepolicies.run.ai" "interactivepolicies.run.ai" "trainingpolicies.run.ai")

# Loop through each CRD API group
for CRD in "${CRDS[@]}"; do
  # Extract the CRD name from the full API group (e.g., distributedpolicies from distributedpolicies.run.ai)
  CRD_NAME=$(echo "$CRD" | cut -d '.' -f 1)

  # Get all namespaces in the cluster
  NAMESPACES=$(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}')

  # Loop through each namespace
  for NAMESPACE in $NAMESPACES; do
    # Get all resources of the current CRD in the current namespace
    RESOURCES=$(kubectl get "$CRD" -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}')

    # Check if any resources were found
    if [ -n "$RESOURCES" ]; then
      # Loop through each resource
      for RESOURCE in $RESOURCES; do
        # Create the filename
        FILENAME="${NAMESPACE}_${RESOURCE}_${CRD_NAME}.yaml"

        # Get the resource as YAML and save it to the file
        kubectl get "$CRD" "$RESOURCE" -n "$NAMESPACE" -o yaml > "$FILENAME"

        echo "Saved $CRD resource '$RESOURCE' from namespace '$NAMESPACE' to file: $FILENAME"
      done
    else
      echo "No $CRD resources found in namespace '$NAMESPACE'."
    fi
  done
done

echo "Script completed."