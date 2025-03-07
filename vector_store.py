import logging
from pymongo import MongoClient
from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
import os
from logger import logger

class SingletonMeta(type):
    """
    A Singleton metaclass that creates only one instance of a class.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class EmbeddingModelManager(metaclass=SingletonMeta):
    """
    Manages the initialization and retrieval of the HuggingFace BGE Embedding model.
    """
    def __init__(self):
        self.model_name = "BAAI/bge-base-en-v1.5"
        self.model_kwargs = {"device": "cpu"}
        self.encode_kwargs = {"normalize_embeddings": True}
        self.embedding_model = None

    def get_embedding_model(self) -> HuggingFaceBgeEmbeddings:
        """
        Returns the HuggingFace BGE Embedding model instance, initializing it if necessary.
        
        Returns:
            HuggingFaceBgeEmbeddings: The embedding model instance.
        """
        if self.embedding_model is None:
            self.embedding_model = HuggingFaceBgeEmbeddings(
                model_name=self.model_name,
                model_kwargs=self.model_kwargs,
                encode_kwargs=self.encode_kwargs
            )
            logger.info("Initialized embedding model.")
        return self.embedding_model

class VectorStoreManager(metaclass=SingletonMeta):
    """
    Manages the initialization and retrieval of the MongoDB Atlas Vector Store.
    """
    def __init__(self):
        self.atlas_connection_string = os.getenv("MONGO_DB_URI")
        self.client = MongoClient(self.atlas_connection_string)
        self.db_name = "VectorDatabase"
        self.collection_name = "VectorCollections"
        self.vector_store = None

    def get_vector_store(self) -> MongoDBAtlasVectorSearch:
        """
        Returns the MongoDB Atlas Vector Store instance, initializing it if necessary.
        
        Returns:
            MongoDBAtlasVectorSearch: The vector store instance.
        """
        if self.vector_store is None:
            atlas_collection = self.client[self.db_name][self.collection_name]
            embedding_model = EmbeddingModelManager().get_embedding_model()
            self.vector_store = MongoDBAtlasVectorSearch(
                embedding=embedding_model,
                collection=atlas_collection
            )
            logger.info("Initialized vector store.")
        return self.vector_store
