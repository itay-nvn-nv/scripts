create namespace
```bash
kubectl create ns webhooks
```

create certificates for webhook server
```bash
openssl req -x509 -newkey rsa:2048 -keyout webhook.key -out webhook.crt -days 365 -nodes -config san.cnf
```

create secret for webhook server certificates
```bash
kubectl -n webhooks create secret tls webhook-tls --key=webhook.key --cert=webhook.crt 
```

create configmap for webhook server python script
```bash
kubectl -n webhooks create configmap webhook-server --from-file=server.py=server.py
```

create base64 encoded string for the webhook.crt file, then place it in `webhooks[0].clientConfig.caBundle` within `MutatingWebhookConfiguration` spec in `manifests.yaml` file.
its crucial that the encoded string will be a single line.
```bash
base64 -w 0 webhook.crt
cat webhook.crt | base64 -w 0
```

apply manifest
```bash
kubectl apply -f manifest.yaml
```

create a test PVC that exceeds 20 GB in size, to see the webhook kick in:
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: example-pvc
  namespace: testing
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 30Gi
EOF
```