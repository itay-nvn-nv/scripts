# Keycloak helm chart
Official website: https://artifacthub.io/packages/helm/bitnami/keycloak

### Add repo
```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### Install chart
```
helm install keycloak bitnami/keycloak \
--create-namespace -n keycloak \
-f values.yaml --debug
```

### Create example entities
Run the script to create a realm, OIDC client and an example user:
```bash
CONTROL_PLANE_URL="https://my-webapp.com" \
KEYCLOAK_ADMIN="root" \
KEYCLOAK_ADMIN_PASSWORD="root" \
KEYCLOAK_URL="https://my-keycloak.com" \
KEYCLOAK_REALM="mytestingrealm" \
USER_FIRST_NAME="Will" \
USER_LAST_NAME="Smith" \
USER_EMAIL="will@gettin-jiggy.io" \
USER_USERNAME="willsmith79" \
USER_PASSWORD="123456" \
KEYCLOAK_CLIENT="myclient" \
bash create_client.sh
```

Modify values according to this table:
| Environment variable | Description | Example |
|--|--|--|
| `CONTROL_PLANE_URL` | The URL of the control plane. | https://my-webapp.com |
| `KEYCLOAK_ADMIN` | Keycloak admin username | root |
| `KEYCLOAK_ADMIN_PASSWORD` | Keycloak admin password | root |
| `KEYCLOAK_URL` | Keycloak URL (hostname), where its expected to be accessed | https://my-keycloak.com |
| `KEYCLOAK_REALM` | The name of the new realm you want to create. | mytestingrealm |
| `KEYCLOAK_CLIENT` | The name of the new OIDC client you want to create. | myclient |
| `USER_FIRST_NAME` | The example user's first name | Will |
| `USER_LAST_NAME` | The example user's last name | Smith |
| `USER_EMAIL` | The example user's email address | will@gettin-jiggy.io |
| `USER_USERNAME` | The example user's username | willsmith79 |
| `USER_PASSWORD` | The example user's initial password (you can require the user to reset it upon login). | 123456 |
