from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo import MongoClient
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_google_genai import GoogleGenerativeAI,ChatGoogleGenerativeAI
# from langchain_huggigface import HuggingFaceEmbeddings
# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings.text2vec import Text2vecEmbeddings

load_dotenv()
# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "mysecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


client = MongoClient(os.getenv("MONGO_DB_URI"))
# users_db = client["chatbot"]
# users_collection = users_db["users"]
# bots_collection = users_db["bots"]

# vectors_db = client["VectorDatabase"]
# chat_history_collection = vectors_db["chatbot-History"]
# vector_collection = vectors_db["VectorCollections"]
# vector_index = "vector_index"
# vector_db_name="VectorDatabase"
# vector_collection_name="VectorCollections"

# client = MongoClient(MONGODB_URI)
# Database and collection names
DB_NAME = "langchain_chatbot"
COLLECTION_NAME = "data"
HISTORY_COLLECTION_NAME = "history"
USERS_COLLECTION_NAME = "users"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "vector_index"
collection = client[DB_NAME][COLLECTION_NAME]


class ListConvertedText2vecEmbeddings(Text2vecEmbeddings):
    def __init__(self, **kwargs):
        # Optionally specify a local model path if you have it downloaded
        # kwargs["model_name_or_path"] = "path/to/local/model"
        super().__init__(**kwargs)
        
    def embed_documents(self, texts):
        return [super().embed_documents(text).tolist() for text in texts]
    
    def embed_query(self, text):
        return super().embed_query(text).tolist()


def llm_model():
    # return GoogleGenerativeAI(model=os.getenv("MODEL_NAME"), google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0, verbose=True, timeout=600)
    return  ChatGoogleGenerativeAI(model=os.getenv("MODEL_NAME"), google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0.7, verbose =True)

def embedding_model():
    return  ListConvertedText2vecEmbeddings()

    #old
    # return HuggingFaceBgeEmbeddings( model_name="BAAI/bge-base-en-v1.5", model_kwargs= {"device": "cpu"}, encode_kwargs= {"normalize_embeddings": True})

def vector_search():
    return MongoDBAtlasVectorSearch.from_connection_string(os.getenv("MONGO_DB_URI"),f"{vector_db_name}.{vector_collection_name}", embedding_model(), index_name=vector_index)

def vector_store():
    return MongoDBAtlasVectorSearch.from_connection_string(
        connection_string=os.getenv("MONGO_DB_URI"),
        namespace=DB_NAME + "." + COLLECTION_NAME,
        embedding=embedding_model(),
        index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
        text_key="content"
    )

    #old
    # return MongoDBAtlasVectorSearch(embedding=embedding_model(),collection=vector_collection)

async def clear_orphaned_history_messages():
    try:
        history_collection = client[DB_NAME][HISTORY_COLLECTION_NAME]
        users_collection = client[DB_NAME][USERS_COLLECTION_NAME]
        user_session_ids = users_collection.distinct("session_id")
        print(f"User session IDs to keep: {user_session_ids}")
        history_session_ids = history_collection.distinct("SessionId")
        print(f"History session IDs found: {history_session_ids}")
        orphaned_session_ids = set(history_session_ids) - set(user_session_ids)
        print(f"Orphaned session IDs to remove: {orphaned_session_ids}")
        if orphaned_session_ids:
            result = history_collection.delete_many({
                "SessionId": {"$in": list(orphaned_session_ids)}
            })
            print(f"Removed {result.deleted_count} orphaned messages from history.")
    except Exception as e:
        print(f"Error in clearing orphaned history messages: {e}")

async def remove_oldest_conversation_if_needed(session_id: str):
    try:
        history_collection = client[DB_NAME][HISTORY_COLLECTION_NAME]
        message_count = history_collection.count_documents({"SessionId": session_id})
        print(f"Total messages for session {session_id}: {message_count}")
        if message_count >= 8:
            oldest_messages = list(history_collection.find({"SessionId": session_id}).sort("_id", ASCENDING).limit(2))
            oldest_ids = [msg["_id"] for msg in oldest_messages]
            print(f"Messages to remove: {oldest_ids}")
            if oldest_ids:
                result = history_collection.delete_many({"_id": {"$in": oldest_ids}})
                print(f"Removed {result.deleted_count} oldest messages for session {session_id}.")
            else:
                print("No messages found to remove.")
    except Exception as e:
        print(f"Error in clearing history for session {session_id}: {e}")