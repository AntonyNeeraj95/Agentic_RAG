from typing import List, Any
import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, Datatype
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

QDRANT_COLLECTION: str = "AgenticRag"
QDRANT_URL: str = os.getenv("QDRANT_URL","http://host.docker.internal:6333")
QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY: str | None = os.getenv("QDRANT_API_KEY")
VECTOR_SIZE: int = 384
BATCH_SIZE: int = 150


def initialize_qdrant_client():
    if QDRANT_URL:
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return QdrantClient(host="localhost", port=QDRANT_PORT, api_key=QDRANT_API_KEY)

client = initialize_qdrant_client()

def check_collection():
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]
    return collection_names


def initialize_collection():
    collection_names = check_collection()
    if QDRANT_COLLECTION not in collection_names:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config={
                "dense": VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE,
                    on_disk=True,
                    datatype=Datatype.FLOAT32,
                )
            }
        )
        print(f"Collection '{QDRANT_COLLECTION}' created!")
        print("**"*50)
    else:
        print(f"Collection '{QDRANT_COLLECTION}' already exists.")
        print("**"*50)


def initialize_vector_store():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    initialize_collection()

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION,
        embedding=embeddings,
        validate_embeddings=True,
        validate_collection_config=True,
        vector_name="dense",
    )
    return vector_store

vector_store = initialize_vector_store()


async def add_documents(documents: List[Any]) -> None:
    """Add documents to the vector store."""
    initialize_collection()
    await vector_store.aadd_documents(documents, batch_size=BATCH_SIZE)
