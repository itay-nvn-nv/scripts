### Create namespace:
kubectl create ns dream

### Apply:
kubectl apply -f crd.yaml
kubectl apply -f deployment.yaml
kubectl apply -f rbac.yaml

### Check logs:
kubectl -n dream logs deploy/dream-controller

### Apply the CR Instance:
kubectl apply -f test_cr_instance.yaml

### Create "clean" deployment for comparision:
kubectl apply -f test_clean_deployment.yaml

### Verify:
kubectl -n runai-test get dreams
kubectl -n runai-test get deployments
kubectl -n runai-test get pods
kubectl -n runai-test get pg

### OPTIONAL: fix
kubectl apply -f rbac_solution.yaml