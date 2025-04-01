import logging
from typing import List
# from data_scrape import categorize_urls, extract_documents_from_urls
# from vector_store import VectorStoreManager
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents.base import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_transformers import LongContextReorder
from pymongo import MongoClient
import jwt
import os
from datetime import datetime, timedelta
from logger import logger
from constants import pwd_context,SECRET_KEY,ALGORITHM, embedding_model, vector_search, vector_store#chat_history_collection,vector_collection
from dotenv import load_dotenv
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from fastapi import HTTPException
import requests
load_dotenv()
#User Authentication
# Utility functions
# MongoDB Client


def get_text_chunks(documents: List[Document]) -> List[Document]:
    """
    Splits the text in a list of LangChain documents into smaller chunks.

    Args:
        documents (List[Document]): A list of LangChain documents to be split.

    Returns:
        List[Document]: A list of LangChain documents with text split into chunks.
    """
    logger.info("Splitting documents into chunks.")
    
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks.")
        return chunks
    
    except Exception as e:
        logger.error(f"Error splitting documents into chunks: {e}")


def add_bot_token_to_docs(documents: List[Document], bot_token: str) -> List[Document]:
    """
    Adds an admin ID to the metadata of each document in the list.

    Args:
        documents (List[Document]): A list of LangChain documents to which the admin ID will be added.
        bot_token (str): The admin ID to be added to the metadata of each document.

    Returns:
        List[Document]: The list of LangChain documents with the admin ID added to their metadata.
    """
    logger.debug("Adding admin ID to documents.")

    try:
        for doc in documents:
            doc.metadata['bot_token'] = bot_token
        
        logger.info(f"Added Bot ID '{bot_token}' to {len(documents)} documents.")
        return documents
    
    except Exception as e:
        logger.error(f"Error adding admin ID '{bot_token}' to documents: {e}")

def data_from_youtube_and_web(urls: List[str]) -> List[Document]:
    """
    Retrieves data from YouTube channels and webpages. 

    Args:
        urls (List[str]): A list of URLs (both web and YouTube) to process.

    Returns:
        List[Document]: A list of LangChain Document objects containing the extracted data.
    """
    logger.info("Starting data retrieval from YouTube and websites")

    try:
        youtube_urls, website_urls = categorize_urls(urls)
        data = []

        # Process website URLs
        logger.info(f"Processing website URLs: {website_urls}")
        try:
            web_data = extract_documents_from_urls(website_urls)
            data.extend(web_data)
        except Exception as e:
            logger.error(f"Failed to get data from website URLs {website_urls}: {e}")
            raise

        # Process YouTube URLs
        # logger.info(f"Processing YouTube URLs: {youtube_urls}")
        # try:
        #     for youtube_url in youtube_urls:
        #         if youtube_url.startswith("@"):
        #             channel_id = get_channel_id(youtube_url)
        #             channel_links = get_channel_videos_links(channel_id)
        #             youtube_data = process_youtube_links(channel_links)
        #         else:
        #             youtube_data = process_youtube_links([youtube_url])
                
        #         data.extend(youtube_data)

        #     logger.info(f"Successfully retrieved data from YouTube URLs.")
        #     return data
        
        # except Exception as e:
        #     logger.error(f"Failed to retrieve data from YouTube URLs: {e}")
        #     raise
        return data
    except Exception as e:
        logger.error(f"Error processing URLs {urls}: {e}")
        raise


def store_user_data(urls: List[str], bot_token: str, file_urls: List[str]) -> bool:
    """
    Processes a list of S3 URLs and user data, adding metadata including admin ID.

    Args:
        urls (List[str]): List of URLs (YouTube and web) to process.
        bot_token (str): Bot ID to add as metadata.
        file_urls (List[str]): List of S3 URLs to process.

    Returns:
        bool: True if data was successfully stored, False otherwise.
    """
    logger.info(f"Storing user data with admin ID: {bot_token}")
    
    try:
        final_user_data = []
        
        # logger.info("Processing S3 URLs.")
        # s3_data = process_s3_urls(file_urls)
        # final_user_data.extend(s3_data)
        # logger.info("Processed S3 URLs successfully.")

        logger.info("Processing YouTube and web URLs.")
        youtube_web_data = data_from_youtube_and_web(urls)
        final_user_data.extend(youtube_web_data)
        
        # Chunk the data for processing
        chunked_data = get_text_chunks(final_user_data)
        
        # Add admin ID to documents
        id_added_data = add_bot_token_to_docs(chunked_data, bot_token)
        
        # Store the documents in the vector store
            
        # vector_store_manager = VectorStoreManager()
        # vector_store= vec

        vector_store.add_documents(id_added_data) 
        logger.info("User data successfully stored in the vector store.")
        
        return True
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        logger.error(f"Error storing user data with ID {bot_token}: {e}")
        return False



def add_message_to_history(question, answer, bot_token, session_id):
    try:
        chat_history_collection.update_one(
            {'session_id': session_id},  # Search query for a document with the given session_id
            {
                '$set': {"bot_token": bot_token},  # Update or set the bot_token field
                '$push': {
                    'chat_history': {  # Push a new chat entry to the 'chat_history' array
                        '$each': [{'timestamp': datetime.utcnow(), 'question': question, 'answer': answer}],  # The new message
                        # '$slice': -20  # Keep only the most recent 20 chat history entries
                    }
                },
                '$setOnInsert': {'created_at': datetime.utcnow()}  # Set 'created_at' only on insert (not update)
            },
            upsert=True  # This option means that if no document is found with the given session_id, a new one will be created
        )
    except Exception as e:
        logger.error(f"Error storing message for session_id: {session_id}, bot token: {bot_token} - {str(e)}")

def get_chat_history(session_id):
    try:
        session = chat_history_collection.find_one({'session_id': session_id}, {'_id': 0, 'chat_history': 1})
        if session and 'chat_history' in session:
            return [(entry['question'], entry['answer']) for entry in session['chat_history']]
        return []
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        logger.error(f"Error fetching chat history for session_id: {session_id} - {str(e)}")

def get_related_docs(bot_token):
    try:

        docs = vector_collection.find({'bot_token':bot_token},{'text':1})
        logger.info(f"Fetched documents for Bot token: {bot_token}")
        return [Document(page_content=doc['text']) for doc in docs]
    except Exception as e:
        logger.info(f"Failed to Fetch Documents from Bot token: {bot_token} , Error : {str(e)}")

def get_ensemble_retriever(bot_token, llm):
    try:
        documents = get_related_docs(bot_token)
        
        retriever = vector_search().as_retriever(
            search_type = "similarity_score_threshold",
            search_kwargs = {
                "k": 4,
                "score_threshold": 0.25,
                "pre_filter": { "bot_token": { "$eq": bot_token } }
            })
        retriever_from_llm=MultiQueryRetriever.from_llm(retriever=retriever,llm=llm)
        # print("Documents : ", documents)
        bm25_retriever = BM25Retriever.from_documents(documents)
        bm25_retriever.k = 3
        logger.info("Ensemble retriever created.")
        return [EnsembleRetriever(retrievers=[bm25_retriever, retriever_from_llm],weights=[0.3, 0.7]),retriever]
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        logger.error(f"Ensemble retriever creation Failed. Bot Token : {bot_token} - Error : {str(e)}")

def get_assistant_details(bot_token:str):
    try:
        url = os.getenv("BACKEND_ENDPOINT")+f"/assistants/get-assistant-details/{bot_token}/"
        response = requests.get(url)
        print(response, url)
        return {"status":response.status_code, "data":response.json()}
    except Exception as e:
        logger.error(f"Failed to Fetch Assistant Details Bot Token: {bot_token} - Error : {str(e)}")
        return {"message":"Failed to fetch assisstant detials", "error":str(e)}

def format_context(docs):
    context_parts = []
    for doc in docs:
        context_parts.append(f"Title: {doc.metadata['title']}\nSummary: {doc.metadata['summary']}\nContent: {doc.page_content}")
    return "\n\n".join(context_parts)

def get_retriever(bot_token):
    retriever = vector_store().as_retriever(search_type="similarity", search_kwargs={"k": 5, "pre_filter": { "bot_token": { "$eq": bot_token } }})
    return retriever