#!/bin/sh
apt-get update && apt-get install -y curl

# if the FASTAPI_ENDPOINT ends with 'azurecontainerapps.io' we will send a request to wake up the backend
if echo "$FASTAPI_ENDPOINT" | grep -q "azurecontainerapps.io"; then
    echo "FASTAPI_ENDPOINT is from Azure Container Apps. Sending request to start the backend..."
    curl -s -o /dev/null "$FASTAPI_ENDPOINT/init-msg"
fi

# Now start 5he ChainLit app
python -m chainlit run app.py --host 0.0.0.0 --port $PORT