# ArgoCD automation script
**saves kubeconfig locally and sets it as default using env var.**

allow script to execute:
```
chmod +x run.sh
```

then run with the name of the ArgoCD app:
```
bash run.sh my-cluster
```

example output:
```
Checking app my-cluster:
app my-cluster is healthy!
kubeconfig file saved at: /Users/johndoe/my-cluster_kubeconfig.yaml
```
