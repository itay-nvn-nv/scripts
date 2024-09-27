# Keycloak helm chart
Official website: https://artifacthub.io/packages/helm/bitnami/keycloak

### Add repo
```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### Modify environment variables
Modify the values in `config.env` file, according to this table:
| Environment variable | Description | Default value |
|--|--|--|
| `HOST_DOMAIN` | base domain | my.domain.com |
| `HOST_PATH` | OPTIONAL: sub path for the domain | /keycloak |
| `HOST_TLS_SECRET` | TLS certificate secret name in the namespace | domain-tls |
| `WEB_APP_URL` | The URL of the web app you wish to integrate SSO with. | https://my-webapp.com |


The following settings are optional, leave as is if unsure:
| Environment variable | Description | Default value |
|--|--|--|
| `KEYCLOAK_ADMIN` | Keycloak admin username | root |
| `KEYCLOAK_ADMIN_PASSWORD` | Keycloak admin password | root |
| `KEYCLOAK_URL` | **DO NOT CHANGE!** Keycloak URL (hostname), where its expected to be accessed | base domain: https://my.domain.com OR subpath: https://my.domain.com/keycloak |
| `KEYCLOAK_REALM` | The name of the new realm you want to create. | mytestingrealm |
| `KEYCLOAK_CLIENT_ID` | Client ID | myclient |
| `KEYCLOAK_CLIENT_TYPE` | Type of client (oidc/saml) | oidc |
| `USER_FIRST_NAME` | The example user's first name | Will |
| `USER_LAST_NAME` | The example user's last name | Smith |
| `USER_EMAIL` | The example user's email address | will@gettin-jiggy.io |
| `USER_USERNAME` | The example user's username | willsmith79 |
| `USER_PASSWORD` | The example user's initial password (you can require the user to reset it upon login). | 123456 |
| `CREATE_CUSTOM_MAPPERS` | Create custom mappers for the clients dedicated scope | false |

when done, set the envs:
```bash
source config.env
```

### Install chart
for sub-path URL, i.e `https://my.domain.com/keycloak`
```bash
helm install keycloak bitnami/keycloak \
--create-namespace -n keycloak \
-f values.yaml \
--set httpRelativePath="$HOST_PATH/" \
--set pathType="Prefix" \
--set ingress.hostname=$HOST_DOMAIN \
--set ingress.extraTls[0].hosts[0]=$HOST_DOMAIN \
--set ingress.extraTls[0].secretName=$HOST_TLS_SECRET \
--debug
```

for base domain URL, i.e `https://my.domain.com`
```bash
helm install keycloak bitnami/keycloak \
--create-namespace -n keycloak \
-f values.yaml \
--set ingress.hostname=$HOST_DOMAIN \
--set ingress.extraTls[0].hosts[0]=$HOST_DOMAIN \
--set ingress.extraTls[0].secretName=$HOST_TLS_SECRET \
--debug

```

wait until keycloak pods are running:
```bash
kubectl -n keycloak get pods
```

### Create example entities

Run the script to create a realm, OIDC client and an example user:
```bash
bash create_client.sh
```
