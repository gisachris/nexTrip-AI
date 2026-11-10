import hashlib
import tiktoken
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from nextrip_ai.core.config import settings

def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def chunk_document(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    chunks = []
    
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(encoding.decode(chunk_tokens))
        if end == len(tokens):
            break
        start += (chunk_size - overlap)
        
    return chunks

def get_embeddings(texts: list[str]) -> list[list[float]]:
    if not settings.OPENAI_API_KEY or "mock" in settings.OPENAI_API_KEY.lower():
        return [[0.0] * 1536 for _ in texts]
        
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [item.embedding for item in response.data]

def upsert_to_pinecone(namespace: str, document_id: str, title: str, chunks: list[str], destination: str, category: str, estimated_cost: str):
    if not settings.PINECONE_API_KEY or "mock" in settings.PINECONE_API_KEY.lower():
        return
        
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    
    index_name = settings.PINECONE_INDEX_NAME
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        
    index = pc.Index(index_name)
    
    # Delete existing chunks for this document
    index.delete(filter={"document_id": document_id}, namespace=namespace)
    
    # Embed chunks
    embeddings = get_embeddings(chunks)
    
    vectors = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        vectors.append({
            "id": f"{document_id}_{idx}",
            "values": embedding,
            "metadata": {
                "document_id": document_id,
                "title": title,
                "text": chunk,
                "category": category,
                "location": destination,
                "estimated_cost": estimated_cost
            }
        })
        
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch, namespace=namespace)
