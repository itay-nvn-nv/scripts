# Keycloak helm chart
Official website: https://artifacthub.io/packages/helm/bitnami/keycloak

### Add repo
```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### Modify values
In the `values.yaml` file there are 2 `ingress` sections, make sure you comment/uncomment them according to the URL convention you wish keycloak to be served on:
| type | example |
|---|---|
| seperate domain | https://my-keycloak.com  |
| subpath on existing domain | https://my-webapp.com/keycloak |

Provide the name of the TLS secret (within the keycloak namespace) for the domain.\
You can leave the rest as is.

### Install chart
```
helm install keycloak bitnami/keycloak \
--create-namespace -n keycloak \
-f values.yaml --debug
```

wait until keycloak pods are running:
```bash
kubectl -n keycloak get pods
```

### Create example entities
Modify the values in `config.env` file, according to this table:
| Environment variable | Description | Default value |
|--|--|--|
| `WEB_APP_URL` | The URL of the web app you wish to integrate SSO with. | https://my-webapp.com |
| `KEYCLOAK_ADMIN` | Keycloak admin username | root |
| `KEYCLOAK_ADMIN_PASSWORD` | Keycloak admin password | root |
| `KEYCLOAK_URL` | Keycloak URL (hostname), where its expected to be accessed | separate domain: https://my-keycloak.com OR subpath: https://my-webapp.com/keycloak |
| `KEYCLOAK_REALM` | The name of the new realm you want to create. | mytestingrealm |
| `KEYCLOAK_CLIENT_ID` | Client ID | myclient |
| `KEYCLOAK_CLIENT_TYPE` | Type of client (oidc/saml) | oidc |
| `USER_FIRST_NAME` | The example user's first name | Will |
| `USER_LAST_NAME` | The example user's last name | Smith |
| `USER_EMAIL` | The example user's email address | will@gettin-jiggy.io |
| `USER_USERNAME` | The example user's username | willsmith79 |
| `USER_PASSWORD` | The example user's initial password (you can require the user to reset it upon login). | 123456 |
| `CREATE_CUSTOM_MAPPERS` | Create custom mappers for the clients dedicated scope | false |

Run the script to create a realm, OIDC client and an example user:
```bash
bash create_client.sh
```
