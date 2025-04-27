#!/bin/bash
echo "Policy exporter script started..."

timestamp=$(date +%Y%m%d_%H%M%S)
folder="runai_exported_policies_$timestamp"
mkdir $folder
cd $folder
echo "Policies output path: $(pwd)"

CRDS=("distributedpolicies.run.ai" "inferencepolicies.run.ai" "interactivepolicies.run.ai" "trainingpolicies.run.ai")

for CRD in "${CRDS[@]}"; do
  CRD_NAME=$(echo "$CRD" | cut -d '.' -f 1)

  NAMESPACES=$(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}')

  for NAMESPACE in $NAMESPACES; do
    RESOURCES=$(kubectl get "$CRD" -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}')

    if [ -n "$RESOURCES" ]; then
      for RESOURCE in $RESOURCES; do
        FILENAME="${CRD_NAME}_${NAMESPACE}_${RESOURCE}.yaml"

        kubectl get "$CRD" "$RESOURCE" -n "$NAMESPACE" -o yaml > "$FILENAME"

        echo "Saved $CRD_NAME '$RESOURCE' from namespace '$NAMESPACE' to file: $FILENAME"
      done
    else
      echo "No $CRD_NAME found in namespace '$NAMESPACE'."
    fi
  done
done

echo "Policy exporter script completed."