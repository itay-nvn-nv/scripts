#!/bin/bash

# Get all nodes and their IPs
echo "Getting node information..."
nodes=$(kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name} {.status.addresses[?(@.type=="InternalIP")].address}{"\n"}{end}')

# Create ConfigMap with node information and test script
echo "Creating ConfigMap..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: node-test-config
data:
  nodes.txt: |
$(echo "$nodes" | sed 's/^/    /')
  test-script.sh: |
    #!/bin/bash
    echo "Pod Name: \$HOSTNAME"
    echo "Pod IP: \$(hostname -i)"
    echo "Service Name: \$SERVICE_NAME"
    echo -e "\nNSLookup test:"
    nslookup \$SERVICE_NAME
    echo -e "\nCurl test:"
    curl -s http://\$SERVICE_NAME:80
EOF

# Create pods and services for each node
echo "$nodes" | while read -r node_name node_ip; do
  pod_name="network-test-${node_name}"
  svc_name="svc-${pod_name}"
  
  echo "Creating pod and service for node: $node_name"
  
  # Create pod with node affinity
  cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: $pod_name
spec:
  containers:
  - name: network-multitool
    image: wbitt/network-multitool
    env:
    - name: SERVICE_NAME
      value: $svc_name
    volumeMounts:
    - name: test-script
      mountPath: /scripts
    command: ["/bin/bash"]
    args: ["-c", "cp /scripts/test-script.sh /tmp/ && chmod +x /tmp/test-script.sh && /tmp/test-script.sh"]
  volumes:
  - name: test-script
    configMap:
      name: node-test-config
      items:
      - key: test-script.sh
        path: test-script.sh
  nodeSelector:
    kubernetes.io/hostname: $node_name
---
apiVersion: v1
kind: Service
metadata:
  name: $svc_name
spec:
  selector:
    kubernetes.io/hostname: $node_name
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF
done

# Wait for pods to be ready
echo -e "\nWaiting for pods to be ready..."
kubectl wait --for=condition=Ready pod -l kubernetes.io/hostname --timeout=60s

# Display results
echo -e "\nResults:"
echo "$nodes" | while read -r node_name node_ip; do
  pod_name="network-test-${node_name}"
  echo -e "\nOutput from pod $pod_name:"
  kubectl logs $pod_name
done