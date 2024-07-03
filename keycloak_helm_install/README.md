# Keycloak helm chart

Add repo:
```
helm repo add bitnami https://charts.bitnami.com/bitnami
```

Install chart:
```
helm install keycloak bitnami/keycloak \
--create-namespace -n keycloak \
-f values.yaml --debug \
```
