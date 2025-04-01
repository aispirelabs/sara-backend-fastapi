from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from validators import ChatRequest, ChatResponse
from constants import llm_model
from utils import  add_message_to_history, get_chat_history, get_ensemble_retriever, get_assistant_details,get_retriever
import uuid
from logger import logger
import asyncio
from bot_response import generate_answer, generate_follow_up_questions, remove_think_step, generate_answer_v2
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import time

load_dotenv()
# Initialize FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat_v1/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handles the chat requests and returns the chatbot's response.

    Args:
        request (ChatRequest): The incoming request containing the question, unique ID, and admin ID.

    Returns:
        ChatResponse: The chatbot's response.
    """
    try:
        # Record the start time
        start_time = time.time()

        llm = llm_model()
        assistant = get_assistant_details(bot_token=request.bot_token)
        print(assistant)

        if not assistant.get('status') == 200:
            return JSONResponse({"message": assistant['data']['message']})

        if assistant['data']['status'] != 'ACTIVE':
            return ChatResponse(answer="Assistant is Not Active Currently. Please contact admin for activation", questions=[])

        chat_history = get_chat_history(request.session_id)
        retrievers = get_ensemble_retriever(request.bot_token, llm)

        prompts = assistant['data']['prompts']
        
        # Perform asynchronous tasks
        follow_up_questions, response = await asyncio.gather(
            generate_follow_up_questions(chat_history, request.question, retrievers[1], llm, prompts=prompts),
            generate_answer(request.question, retrievers[0], chat_history, llm, prompts=prompts)
        )

        if not response.strip():
            response = "Could you Please rephrase the question with more context?"
        if response.startswith("AI:"):
            response = response[len("AI:"):].strip()

        response = remove_think_step(response)
        add_message_to_history(request.question, response, request.bot_token, request.session_id)

        # Calculate the elapsed time
        elapsed_time = time.time() - start_time
        print(f"Response time: {elapsed_time:.4f} seconds")

        return ChatResponse(answer=response, questions=follow_up_questions["questions"])

    except Exception as e:
        logger.error(f"Error handling chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# from test import main_#?chatbot
@app.post("/chat/", response_model=ChatResponse)
async def chat_v2(request: ChatRequest):
    try:
        # Record the start time
        start_time = time.time()

        llm = llm_model()
        assistant = get_assistant_details(bot_token=request.bot_token)
        print(assistant)

        if not assistant.get('status') == 200:
            return JSONResponse({"message": assistant['data']['message']})

        if assistant['data']['status'] != 'ACTIVE':
            return ChatResponse(answer="Assistant is Not Active Currently. Please contact admin for activation", questions=[])

        # chat_history = get_chat_history(request.session_id)
        retrievers = get_retriever(request.bot_token)

        prompts = assistant['data']['prompts']
        
        # Perform asynchronous tasks
        # follow_up_questions, response = await asyncio.gather(
        #     generate_follow_up_questions(chat_history, request.question, retrievers[1], llm, prompts=prompts),
        #     generate_answer(request.question, retrievers[0], chat_history, llm, prompts=prompts)
        # )
        response = await generate_answer_v2(request.question, request.session_id, retrievers, llm, prompts)

        # if not response.strip():
        #     response = "Could you Please rephrase the question with more context?"
        # if response.startswith("AI:"):
        #     response = response[len("AI:"):].strip()

        # response = remove_think_step(response)
        add_message_to_history(request.question, response['answer'], request.bot_token, request.session_id)

        # Calculate the elapsed time
        elapsed_time = time.time() - start_time
        print(f"Response time: {elapsed_time:.4f} seconds")

        return ChatResponse(answer=response['answer'], questions=[])#follow_up_questions["questions"])

    except Exception as e:
        print("RESPONSE = ", response)
        logger.error(f"Error handling chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
