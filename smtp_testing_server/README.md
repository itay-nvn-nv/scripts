# SMTP Testing Server

Kubernetes-native SMTP test server using MailHog. Catches emails without delivering them - perfect for testing your webapp's email functionality.

## Quick Start

```bash
# Deploy the server (no authentication)
kubectl apply -f namespace.yaml
kubectl apply -f mailhog-deployment.yaml
kubectl apply -f mailhog-service.yaml
kubectl apply -f smtp-config.yaml
kubectl apply -f smtp-credentials-secret.yaml

# Access web interface to view caught emails
kubectl port-forward -n smtp service/mailhog 8025:8025
# Open: http://localhost:8025
```

## SMTP Connection Settings

**Default (No Authentication):**
- Host: `mailhog.smtp.svc.cluster.local`
- Port: `1025`
- Username/Password: *(empty)*
- TLS: Disabled

**With Authentication:**
- Host: `mailhog.smtp.svc.cluster.local`
- Port: `1025`
- Username: `testuser`
- Password: `testpass`
- TLS: Disabled

## Switch Authentication Mode

**Enable Authentication:**
```bash
kubectl apply -f smtp-config-auth.yaml
kubectl rollout restart deployment/mailhog -n smtp
```

**Disable Authentication:**
```bash
kubectl apply -f smtp-config-noauth.yaml
kubectl rollout restart deployment/mailhog -n smtp
```

## Custom Credentials

To change the default `testuser:testpass`:

1. **Edit `smtp-config-auth.yaml`** - Update SMTP_USERNAME and SMTP_PASSWORD
2. **Edit `smtp-credentials-secret.yaml`** - Update the base64 encoded auth string:
   ```bash
   echo -n "myuser:mypass" | base64
   ```
3. **Apply changes:**
   ```bash
   kubectl apply -f smtp-credentials-secret.yaml smtp-config-auth.yaml
   kubectl rollout restart deployment/mailhog -n smtp
   ```

## Cleanup

```bash
kubectl delete -f .
```
