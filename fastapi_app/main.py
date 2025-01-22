import os
from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from utils.QAPipeline import QAPipeline
from utils.setup import (
    initialize_llm,
    initialize_vector_search,
    load_config,
    load_env_vars,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize some configs in the app state."""
    # Enable Langsmith tracing
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    
    session_env = load_env_vars()
    session_config = load_config()
    llm = initialize_llm(session_env, session_config)
    vector_search = initialize_vector_search(session_env, session_config)
    app.state.course_name = session_config['COURSE_NAME']
    app.state.qa_pipeline = QAPipeline(llm, vector_search, course_name=session_config['COURSE_NAME'])
    yield

app = FastAPI(lifespan=lifespan)

class QueryRequest(BaseModel):
    query: str
    response_type: str = "recommendation"
    content_type_filter: Optional[str] = None

class Citation(BaseModel):
    url: str
    title: str
    content_type: str
    
class Response(BaseModel):
    answer: str
    citations: Dict[int, Citation] 

@app.get("/init-msg", summary="Initializes the chat message.")
def initialize_chat():
    message = f"""Hi, I am UC Online Copilot which can help you learn about {app.state.course_name}.
Ask me anything related to the course, and I will try to answer based on the course content!"""
    return {"message": message}

@app.post("/ask", response_model=Response, summary="Ask questions related to the course content.", 
        description="Submit a question to the QA pipeline and retrieve an answer or recommendation with citations of relevant course content.")
async def ask_question(request: QueryRequest):
    query = request.query
    response_type = request.response_type
    content_type_filter = request.content_type_filter
    
    try:
        response = app.state.qa_pipeline.run(query=query, response_type=response_type, content_type_filter=content_type_filter)
        answer = response["content"]
        citations = response["citation"]
        return Response(answer=answer, citations=citations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the query: {str(e)}")