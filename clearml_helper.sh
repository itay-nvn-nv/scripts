apt update && apt install -y curl jq

random_digits=$(printf "%03d" "$((RANDOM % 1000))")
PROJECT_NAME="test-$MY_POD_NAMESPACE-$random_digits"
QUEUE_NAME=$MY_POD_NAMESPACE

echo "WEBSERVER_URL: $WEBSERVER_URL"
echo "WEBSERVER_BASIC_AUTH: $WEBSERVER_BASIC_AUTH"
echo "PROJECT_NAME: $PROJECT_NAME"
echo "QUEUE_NAME: $QUEUE_NAME"

CLEARML_TOKEN=$(curl -s --location --request POST "$WEBSERVER_URL/api/v2.30/auth.login" \
--header "Authorization: Basic $WEBSERVER_BASIC_AUTH" \
--header "Origin: $WEBSERVER_URL" \
--header "Referer: $WEBSERVER_URL/login" \
--header 'X-Allegro-Client: Webapp-1.16.2-502' \
--header 'X-Clearml-Impersonate-As: __tests__' | jq -r '.data.token')

echo "CLEARML_TOKEN: $CLEARML_TOKEN"
echo

# 2) create project (always random and unique)
echo "creating new project: $PROJECT_NAME"
PROJECT_RESPONSE=$(curl -s --location "$WEBSERVER_URL/api/v2.30/projects.create" \
--header "Cookie: clearml-token-k8s=$CLEARML_TOKEN" \
--header 'Content-Type: application/json' \
--data "{\"name\": \"$PROJECT_NAME\",\"description\": \"test in progress\",\"system_tags\": [],\"default_output_destination\": null}")
PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.data.id')
echo "PROJECT_ID: $PROJECT_ID"
echo

# 3) check if queue exists and create if needed
echo "Checking if queue exists: $QUEUE_NAME"
QUEUE_ID=$(curl -s --location "$WEBSERVER_URL/api/v2.30/queues.get_all" \
--header "Cookie: clearml-token-k8s=$CLEARML_TOKEN" \
--header 'Content-Type: application/json' | jq -r ".data.queues[] | select(.name == \"$QUEUE_NAME\") | .id")

if [ -z "$QUEUE_ID" ]; then
    echo "Queue does not exist, creating new queue: $QUEUE_NAME"
    QUEUE_ID=$(curl -s --location "$WEBSERVER_URL/api/v2.30/queues.create" \
    --header "Cookie: clearml-token-k8s=$CLEARML_TOKEN" \
    --header 'Content-Type: application/json' \
    --data "{\"name\": \"$QUEUE_NAME\"}" | jq -r '.data.id')
else
    echo "Queue already exists with ID: $QUEUE_ID"
fi
echo "QUEUE_ID: $QUEUE_ID"
echo
