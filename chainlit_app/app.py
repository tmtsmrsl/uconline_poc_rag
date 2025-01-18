import os
from typing import Dict, List
from urllib.parse import urljoin

import chainlit as cl
import requests
from chainlit.input_widget import Select
from dotenv import load_dotenv

from utils.AnswerFormatter import AnswerFormatter

load_dotenv()

async def warm_up_endpoint():
    try:
        endpoint = urljoin(cl.user_session.get('fastapi_endpoint'), '/init-msg')
        response = await cl.make_async(requests.get)(endpoint, timeout=60)
        response.raise_for_status()
        message = response.json()['message']
        return message
    except requests.exceptions.RequestException as e:
        raise Exception(f"An Error occured when fetching response from the /init-msg GET endpoint: {str(e)}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")
        
@cl.on_settings_update
async def update_settings(settings):
    """Update the settings in the user session."""
    response_type_dict = {"Resource Recommendation": "recommendation", "Direct Answer": "answer"}
    cl.user_session.set("response_type", response_type_dict[settings["response_type"]])
    
@cl.on_chat_start
async def start():
    cl.user_session.set("fastapi_endpoint", os.getenv("FASTAPI_ENDPOINT"))
    
    # Setup the settings interface
    settings = await cl.ChatSettings(
        [
            Select(
                id="response_type",
                label="Response Type",
                values=["Resource Recommendation", "Direct Answer"],
                initial_index=0,
            ),
        ]
    ).send()
    await update_settings(settings)
    
    wait_msg = await cl.Message(content="Preparing the chat session. Please wait a moment...").send()
    
    try:
        initial_msg = await warm_up_endpoint()
        await wait_msg.remove()
        await cl.Message(content=initial_msg).send()
        
    except Exception as e:
        await wait_msg.remove()
        await cl.Message(content=str(e)).send()
    
@cl.on_message
async def main(message: cl.Message):
    wait_msg = await cl.Message(content="Searching through the course materials...").send()
    
    # Prepare the request payload for the FastAPI endpoint
    payload = {
        "query": message.content,
        "response_type": cl.user_session.get("response_type")
    }
    
    try:
        # Send the request to the FastAPI endpoint
        endpoint = urljoin(cl.user_session.get("fastapi_endpoint"), '/ask')
        response = await cl.make_async(requests.post)(endpoint, json=payload, timeout=60)
        response.raise_for_status() 
        result = response.json()
        
        answer = result["answer"]
        citations = result["citations"]
        
        await wait_msg.remove()
        await AnswerFormatter().send_msg(answer, citations)
        
    except requests.exceptions.HTTPError as e:
        await cl.Message(content=f"An Error occured when fetching response from the /ask POST endpoint. Please contact the administrator.").send()
        
    except Exception as e:
        await cl.Message(content=f"An unexpected error occurred. Please contact the administrator.").send()
