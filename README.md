## FastAPI endpoint 
The FastAPI endpoint acts as a backend for the RAG pipeline. It receives a question from the user and returns a response. 

### Deploying locally
Run the command below from the `fastapi_app` directory to start the FastAPI app on your local machine.
```bash
uvicorn main:app --reload --port 8010
```

Example request to the FastAPI endpoint:
```bash
curl -X GET http://localhost:8010/init-msg
```
This will return a welcome message from the FastAPI endpoint.

```bash
curl -X 'POST' \
  'localhost:8010/ask' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "How can we support indigenous sustainability?",
    "response_type": "recommendation"
  }'
```
Response types can be either `recommendation` (does not provide direct answer, but recommends relevant materials related to the question) or `answer` (provides direct answer to the question).

## Deploying to Azure Container App
First build the Docker image and run the container locally to test the deployment. 
```bash
docker build -t uconline-copilot-backend:latest .
```

Create a network so that the FastAPI container and the Chainlit container can communicate with each other.
```bash
docker network create app-network
docker run -it --name backend -p 8010:8010 --env-file .env --network app-network uconline-copilot-backend:latest  
```
You can test the endpoint using the same request as shown in the previous section. DO NOT change the `localhost` to `0:0:0:0`.

If the container runs successfully, push the image to Azure Container App.
```bash
az containerapp up --resource-group uconline-copilot --name backend --ingress external --target-port 8010 --source . --location australiaeast
``` 

If the deployment is successful, the container app endpoint will be displayed in the terminal. For example:
```bash
Container app created. Access your app at https://backend.bluepond-305ce4f5.australiaeast.azurecontainerapps.io/ 
```

IMPORTANT: Make sure to set the environment variables of the container app via the Azure portal (similar to the `.env` file) and redeploy the container app.
You can test the deployed endpoint using similar request as shown in the previous section, but replace `localhost:8010` with the endpoint provided by Azure Container App. For example:
```bash
curl -X 'POST' \
  'https://backend.bluepond-305ce4f5.australiaeast.azurecontainerapps.io/' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "How can we support indigenous sustainability?",
    "response_type": "recommendation"
  }'
```

## Chainlit App
The Chainlit app is a frontend for the RAG pipeline. It provides a chat interface for the user to ask questions and receive responses (which are processed by the FastAPI endpoint).

### Deploying locally
You can run the command below from the `chainlit_app` directory to start the Chainlit app on your local machine. Make sure to set the `FASTAPI_ENDPOINT` on `.env` to the appropriate FastAPI endpoint URL.
```bash
python -m chainlit run app.py -w --port 8000
```
The Chainlit app will run on `http://localhost:8000`. 

### Deploying to Azure Container App
First build the Docker image and run the container locally to test the deployment. 
```bash
docker build -t uconline-copilot-frontend:latest .
```

Run the container under the same network as the FastAPI container, and set the `FASTAPI_ENDPOINT` environment variable to the `{NAME}:{PORT}` of the FastAPI container created earlier.
```bash
docker run -it --name frontend -p 8000:8000 --network app-network -e FASTAPI_ENDPOINT=http://backend:8010 uconline-copilot-frontend:latest
```
You can test the endpoint using the same request as shown in the previous section. DO NOT change the `localhost` to `0:0:0:0`.

If the container runs successfully, push the image to Azure Container App.
```bash
az containerapp up --resource-group uconline-copilot --name frontend --ingress external --target-port 8000 --source . --location australiaeast --env-vars FASTAPI_ENDPOINT=https://backend.bluepond-305ce4f5.australiaeast.azurecontainerapps.io/
``` 

If the deployment is successful, the container app endpoint will be displayed in the terminal. For example:
```bash
Container app created. Access your app at https://frontend.bluepond-305ce4f5.australiaeast.azurecontainerapps.io/
```
