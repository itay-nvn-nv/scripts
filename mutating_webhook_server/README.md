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
```

apply all manifests
```bash
kubectl apply -f manifests.yaml
```

create a test pod, then verify the additional container was properly injected.
```bash
kubectl run test-pod --image=ubuntu --namespace=testing -- sleep infinity
```