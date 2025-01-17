import os
from typing import Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from fastapi_app.utils import config
from fastapi_app.utils.AzureVectorSearch import AzureVectorSearch
from fastapi_app.utils.QAPipeline import QAPipeline


def load_env_vars() -> Dict:
    """Load environment variables from the .env file."""
    load_dotenv()
    session_env = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "LANGCHAIN_API_KEY": os.getenv("LANGCHAIN_API_KEY"),
        "AZURE_SEARCH_ENDPOINT": os.getenv("AZURE_SEARCH_ENDPOINT"),
        "AZURE_SEARCH_KEY": os.getenv("AZURE_SEARCH_KEY"),
    }
    return session_env

    
def load_config() -> Dict:
    """Load configuration settings for the app."""
    session_config = {
        "AZURE_INDEX_NAME": config.AZURE_INDEX_NAME,
        "COURSE_NAME": config.COURSE_NAME,
        "LLM_TEMPERATURE": config.LLM_TEMPERATURE,
        "LLM_MAX_RETRIES": config.LLM_MAX_RETRIES,
        "OUTPUT_FIELDS": config.OUTPUT_FIELDS
    }
    return session_config

def initialize_vector_search(session_env: Dict, session_config: Dict) -> AzureVectorSearch:
    embedding_model = OpenAIEmbeddings(openai_api_key=session_env["OPENAI_API_KEY"], model="text-embedding-3-large")
        
    return AzureVectorSearch(session_env["AZURE_SEARCH_ENDPOINT"], session_env["AZURE_SEARCH_KEY"], session_config['AZURE_INDEX_NAME'], 
                            embedding_model, session_config['OUTPUT_FIELDS'])

def initialize_llm(session_env: Dict, session_config: Dict) -> ChatOpenAI:
    return ChatOpenAI(
        api_key=session_env['OPENAI_API_KEY'],
        model="gpt-4o",
        temperature=session_config['LLM_TEMPERATURE'],
        max_retries=session_config['LLM_MAX_RETRIES'])
    
