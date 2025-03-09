from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo import MongoClient
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
# from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_google_genai import GoogleGenerativeAI
# from langchain_huggigface import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

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
users_db = client["chatbot"]
users_collection = users_db["users"]
bots_collection = users_db["bots"]

vectors_db = client["VectorDatabase"]
chat_history_collection = vectors_db["chatbot-History"]
vector_collection = vectors_db["VectorCollections"]
vector_index = "vector_index"
vector_db_name="VectorDatabase"
vector_collection_name="VectorCollections"


def llm_model():
    return GoogleGenerativeAI(model=os.getenv("MODEL_NAME"), google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0, verbose=True, timeout=600)

def embedding_model():
    return HuggingFaceEmbeddings( model_name="BAAI/bge-base-en-v1.5", model_kwargs= {"device": "cpu"}, encode_kwargs= {"normalize_embeddings": True})

def vector_search():
    return MongoDBAtlasVectorSearch.from_connection_string(os.getenv("MONGO_DB_URI"),f"{vector_db_name}.{vector_collection_name}", embedding_model(), index_name=vector_index)

def vector_store():
    return MongoDBAtlasVectorSearch(embedding=embedding_model(),collection=vector_collection)