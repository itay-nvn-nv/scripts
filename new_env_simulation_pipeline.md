new env simulation pipeline:

## download kubeconfig and place
```
export KUBECONFIG=$KC_PATH
```

## run cli downloader
```
bash ~/scripts/cli_downloader.sh
```

## modify kubeconfig:
```
python3 ~/scripts/envinaclick_kubeconfig_modifier.py \
--input-yaml $KC_PATH \
```

## get token:
```
bash ~/scripts/get_temp_token.sh $EMAIL $PASSWORD $CTRL_PLANE_URL $KEYCLOAK_URL $KEYCLOAK_REALM
```

## create GPU workload:
```
runai submit \
--job-name-prefix cpu-test \
--gpu 1 \
--image nginx \
--command -- sleep infinity
```
## create CPU workloads:
```
runai submit \
--job-name-prefix gpu-test \
--image nginx \
--command -- sleep infinity
```

helm -n runai upgrade \
runai-cluster runai/runai-cluster \
--version 2.19.10 \
--debug