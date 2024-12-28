# argo-workflow

# install argo (pointing to "hello" project on "runai-hello" namespace)

kubectl create namespace argo

kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.5.2/install.yaml

kubectl create clusterrolebinding system:serviceaccount:runai-hello:default --clusterrole=cluster-admin --serviceaccount=runai-hello:default

kubectl patch deployment \
  argo-server \
  --namespace argo \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/args", "value": [
  "server",
  "--auth-mode=server"
]}]'
 