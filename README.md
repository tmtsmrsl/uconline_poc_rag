This repository contains the RAG pipeline implementation for the course chatbot, allowing users to ask questions related to the course and receive responses that are justified by the course contents.

Ensure that you have run the ETL pipeline ([uconline_poc_etl](https://github.com/tmtsmrsl/uconline_poc_etl)) to extract and store all module materials in the vector database.

Tech stacks:
- Backend: FastAPI
- Frontend: Chainlit
- Vector database: Azure Search
- Embeddings model: OpenAI text-embedding-3-large
- LLM: OpenAI gpt-4o
- LLM Orchestration: Langgraph
- LLMOps: Langsmith
- Container deployment: Azure Container Apps

## Architecture of the RAG Pipeline

![image](https://github.com/user-attachments/assets/b8d5e64e-f4e2-497e-9640-29f8b2584375)

1. Guardrail: Use LLM to filter out questions that violate the pre-defined guardrail criteria.
2. Retrieve: Retrieve the relevant documents from the vector database using hybrid search (dense and sparse embeddings). These documents are then further reranked using the semantic reranker to ensure high-quality retrieval results. The retrieved documents are split based on the lesson blocks or timestamps and formatted with an intermediate ID so the LLM can easily refer to it in step 3.
3. Generate: Use LLM to generate an answer with inline citation based on the documents retrieved from step 2 and the user’s question.
4. Format Answer: Refines the generated answer by reformatting the intermediate IDs and linking them to the original sources, ensuring traceability. Questions filtered out in step 1 still go through this step to ensure a consistent format for the final answer.

## FastAPI endpoint 
The FastAPI endpoint acts as a backend for the RAG pipeline. It receives a question from the user and returns a response. 

### Deploying locally
Go to the `fastapi_app` directory.
```bash
cd fastapi_app
```
Make sure to have a `.env` file in the `fastapi_app` directory following the format on the `.env.sample` file.

For first-timer, create a virtual environment and install the dependencies.
```bash
python -m venv fastapi.venv
source fastapi.venv/Scripts/activate 
python -m pip install -r requirements.txt
```

Next time you only need to activate the virtual environment.
```bash
source fastapi.venv/Scripts/activate 
```

Run the command below to start the FastAPI app on your local machine.
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
docker run -it --rm --name backend -p 8010:8010 --env-file .env --network app-network uconline-copilot-backend:latest  
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
Go to the `chainlit_app` directory.
```bash
cd chainlit_app
```
Make sure to have a `.env` file in the `chainlit_app` directory following the format on the `.env.sample` file.

For first-timer, create a virtual environment and install the dependencies.
```bash
python -m venv chainlit.venv
source chainlit.venv/Scripts/activate
python -m pip install -r requirements.txt
```

Next time you only need to activate the virtual environment.
```bash
source chainlit.venv/Scripts/activate
```

You can run the command below to start the Chainlit app on your local machine. Make sure to set the `FASTAPI_ENDPOINT` on `.env` to the appropriate FastAPI endpoint URL.
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
docker run -it --rm --name frontend -p 8000:8000 --network app-network -e FASTAPI_ENDPOINT=http://backend:8010 uconline-copilot-frontend:latest
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

## Chrome Extension
### Installing from Chrome Web Store
1. Rise Autoscroller: https://chromewebstore.google.com/detail/rise-autoscroller/eokedfpaaofokboekkgbhckmeocfdmdi  
Highlight specific lesson blocks on a submodule, and allow users to automatically scroll between highlighted blocks. Simply add "/block/{block_1},{block_2}" after the original submodule URL.

2. Echo360 Autojumper: https://chromewebstore.google.com/detail/echo360-autojumper/hbfkmncogocdafemfoideejidpncgnao  
Allow users to jump to a specific timestamp of a video hosted on echo360.net.au, by adding "t" parameter (in seconds) to the embed URL.

### Installing from Local Folder
To install the extension from local folder, follow the steps below:
1. Open the Extension Management page by navigating to `chrome://extensions`.
2. Enable Developer Mode by clicking the toggle switch on the top right corner of the page.
3. Click the "Load unpacked" button and select the `echo360_autojumper` or `rise_autoscroller` directory.


