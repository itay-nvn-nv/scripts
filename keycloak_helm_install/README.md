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

Run initialization script to create realm and entities:
```
bash initialization.sh
```

OPTIONAL: Upgrade chart:
```
helm upgrade keycloak bitnami/keycloak \
 -n keycloak -f values.yaml --debug
```
