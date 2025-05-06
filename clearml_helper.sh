WEBSERVER_URL="http://clearml-webserver.clearml.svc.cluster.local:8080"
WEBSERVER_BASIC_AUTH="R0dTOUY0TTZYQjJEWEo1QUZUOUY6Mm9HdWpWRmhQZmFvemhwdXoyR3pRZkE1T3l4bU1zUjNXVkpwc0NSNWhyZ0hGczIwUE8="

PROJECT_NAME="test-999-$MY_POD_NAMESPACE"
QUEUE_NAME=$MY_POD_NAMESPACE

CLEARML_TOKEN=$(curl -s --location --request POST "$WEBSERVER_URL/api/v2.30/auth.login" \
--header "Authorization: Basic $WEBSERVER_BASIC_AUTH" \
--header "Origin: $WEBSERVER_URL" \
--header "Referer: $WEBSERVER_URL/login" \
--header 'X-Allegro-Client: Webapp-1.16.2-502' \
--header 'X-Clearml-Impersonate-As: __tests__' | jq -r '.data.token')

echo "CLEARML_TOKEN: $CLEARML_TOKEN"
echo

# 2) create project
echo "creating new project: $PROJECT_NAME"
PROJECT_RESPONSE=$(curl -s --location "$WEBSERVER_URL/api/v2.30/projects.create" \
--header "Cookie: clearml-token-k8s=$CLEARML_TOKEN" \
--header 'Content-Type: application/json' \
--data "{\"name\": \"$PROJECT_NAME\",\"description\": \"test in progress\",\"system_tags\": [],\"default_output_destination\": null}")
PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.data.id')
echo "PROJECT_ID: $PROJECT_ID"
echo

# 3) create queue
echo "creating new queue: $QUEUE_NAME"
QUEUE_ID=$(curl -s --location "$WEBSERVER_URL/api/v2.30/queues.create" \
--header "Cookie: clearml-token-k8s=$CLEARML_TOKEN" \
--header 'Content-Type: application/json' \
--data "{\"name\": \"$QUEUE_NAME\"}" | jq -r '.data.id')
echo "QUEUE_ID: $QUEUE_ID"
echo