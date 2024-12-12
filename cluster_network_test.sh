#!/bin/bash

echo-color() {
    # Expanded array of rainbow and vibrant colors
    local colors=(
        "\033[31m"  # Red
        "\033[91m"  # Bright Red
        "\033[33m"  # Yellow/Orange
        "\033[93m"  # Bright Yellow
        "\033[32m"  # Green
        "\033[92m"  # Bright Green
        "\033[36m"  # Cyan
        "\033[96m"  # Bright Cyan
        "\033[34m"  # Blue
        "\033[94m"  # Bright Blue
        "\033[35m"  # Magenta
        "\033[95m"  # Bright Magenta
    )

    # Reset color code
    local reset="\033[0m"

    # Select a random color from the array
    local random_color=${colors[$((RANDOM % ${#colors[@]}))]}
    
    # Print the input text with the random color
    echo -e "${random_color}${*}${reset}"
}

# Define constants
NAMESPACE="network-test"
TEST_POD_BASE="test-pod"
TEST_SVC_BASE="test-svc"
TEST_IMAGE="cyberdog123/http_echo_hello_world"

echo-color "=== Node list: ==="
kubectl get nodes -o "custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,K8S_VERSION:.status.nodeInfo.kubeletVersion,CONTAINERD:.status.nodeInfo.containerRuntimeVersion,OS:.status.nodeInfo.osImage,CPU_TOTAL:.status.capacity.cpu,CPU_USED:.status.allocatable.cpu,MEMORY_TOTAL:.status.capacity.memory,MEMORY_USED:.status.allocatable.memory,GPU_TOTAL:.status.capacity.\"nvidia.com/gpu\",GPU_USED:.status.allocatable.\"nvidia.com/gpu\""

# Create a namespace for testing
echo-color "=== Creating namespace '$NAMESPACE'... ==="
kubectl create namespace $NAMESPACE || echo-color "=== Namespace $NAMESPACE already exists. ==="

# Get node names
echo-color "=== Retrieving node names... ==="
NODE_NAMES=$(kubectl get nodes -o jsonpath='{.items[*].metadata.name}')

# Deploy a pod and service on each node
echo-color "=== Creating test pods and services on each node... ==="
for NODE in $NODE_NAMES; do
    POD_NAME="${TEST_POD_BASE}-${NODE}"
    SVC_NAME="${TEST_SVC_BASE}-${NODE}"

    # Create a pod on the node
    kubectl run $POD_NAME --image=$TEST_IMAGE --restart=Never --overrides='
    {
      "apiVersion": "v1",
      "metadata": {"labels": {"mission":"torun"}},
      "spec": {
        "nodeName": "'$NODE'",
        "containers": [{
          "name": "http-echo",
          "image": "'$TEST_IMAGE'",
          "ports": [{"containerPort": 80}]
        },
        {"name": "nginx",
          "image": "nginx",
          "command": ["sleep", "infinity"],
          "ports": [{"containerPort": 9999}]
        }]
      }
    }' -n $NAMESPACE &> /dev/null || echo-color "=== Pod $POD_NAME already exists. ==="

    # Expose the pod as a ClusterIP service
    kubectl expose pod $POD_NAME --port=80 --target-port=80 --name=$SVC_NAME -n $NAMESPACE &> /dev/null || echo-color "=== Service $SVC_NAME already exists. ==="
done

# Wait for pods to be ready
echo-color "=== Waiting for test pods to be ready... ==="
kubectl wait --for=condition=Ready pods -l mission=torun --timeout=60s -n $NAMESPACE || {
    echo-color "=== Some pods failed to become ready. Exiting... ==="
    exit 1
}

# Test DNS resolution and connectivity
echo -e "\nTesting DNS resolution and connectivity between pods... ==="
for SRC_NODE in $NODE_NAMES; do
    SRC_POD="${TEST_POD_BASE}-${SRC_NODE}"
    for DST_NODE in $NODE_NAMES; do
        if [ "$SRC_NODE" != "$DST_NODE" ]; then
            DST_SVC="${TEST_SVC_BASE}-${DST_NODE}"
            echo-color "=== From pod '$SRC_POD' to service '$DST_SVC':"
            kubectl exec -n $NAMESPACE $SRC_POD -c nginx -- curl -s $DST_SVC.$NAMESPACE.svc.cluster.local && echo
        fi
    done
done

# Cleanup resources
echo-color "=== Cleaning up test resources... ==="
kubectl delete namespace $NAMESPACE --wait &> /dev/null || echo-color "=== Failed to delete namespace $NAMESPACE. ==="

echo-color "=== DNS resolution and inter-pod communication test complete. ==="

echo-color "=== kube-system: ==="
kubectl -n kube-system get pods -o wide

echo-color "=== NVIDIA GPU Operator: ==="
kubectl -n gpu-operator get pods -o wide
