#!/bin/bash

threshold_date="2024-09-01T00:00:00Z"

kubectl get tw --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.status.completionTime}{"\n"}{end}' | \
while IFS=$'\t' read -r namespace name completion_time; do
  if [[ -n "$completion_time" && "$completion_time" < "$threshold_date" ]]; then
    kubectl delete tw -n $namespace $name --wait=false
  fi
done

echo "Deletion process completed."
