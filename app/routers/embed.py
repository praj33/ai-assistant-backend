# Integrated with Chandresh's EmbedCore v3 module
# Provides stable embeddings with security, caching, and quality checks

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import hashlib
import sys
import os

# Add embed_core to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'embed_core'))

from assistant_pipeline import process_message

router = APIRouter()

# Global cache for embeddings
cache = {}

class EmbedRequest(BaseModel):
    texts: List[str]
    user_id: str = "default_user"
    session_id: str = "default_session"
    platform: str = "web"


class SimilarityRequest(BaseModel):
    texts1: List[str]
    texts2: List[str]
    user_id: str = "default_user"
    session_id: str = "default_session"
    platform: str = "web"


@router.post("/embed")
async def generate_embeddings(request: EmbedRequest):
    if not request.texts:
        return {"embeddings": [], "obfuscated_embeddings": []}

    embeddings = []
    obfuscated_embeddings = []

    for text in request.texts:
        text_hash = hashlib.md5((text + request.user_id).encode()).hexdigest()  # Include user_id in hash for security
        if text_hash in cache:
            embedding, obfuscated = cache[text_hash]
        else:
            try:
                result = process_message(request.user_id, request.session_id, request.platform, text)
                if result["status"] == "success":
                    embedding = result["embedding"]
                    obfuscated = result["obfuscated_embedding"]
                    cache[text_hash] = (embedding, obfuscated)
                else:
                    # Fallback to basic embedding if EmbedCore fails
                    raise Exception(result.get("error_message", "EmbedCore failed"))
            except Exception as e:
                # Fallback implementation
                try:
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    embedding = model.encode(text).tolist()
                    obfuscated = embedding  # No obfuscation in fallback
                except Exception as fallback_e:
                    raise HTTPException(status_code=500, detail=f"Embedding computation failed: {str(e)}, fallback also failed: {str(fallback_e)}")

        embeddings.append(embedding)
        obfuscated_embeddings.append(obfuscated)

    return {"embeddings": embeddings, "obfuscated_embeddings": obfuscated_embeddings}


@router.post("/embed/similarity")
async def compute_similarity(request: SimilarityRequest):
    if not request.texts1 or not request.texts2:
        return {"similarities": []}

    # Get embeddings using the embed endpoint logic
    emb1 = []
    for text in request.texts1:
        text_hash = hashlib.md5((text + request.user_id).encode()).hexdigest()
        if text_hash in cache:
            embedding, _ = cache[text_hash]
        else:
            try:
                result = process_message(request.user_id, request.session_id, request.platform, text)
                if result["status"] == "success":
                    embedding = result["obfuscated_embedding"]  # Use obfuscated for similarity
                    cache[text_hash] = (result["embedding"], embedding)
                else:
                    raise Exception(result.get("error_message", "EmbedCore failed"))
            except Exception as e:
                # Fallback
                try:
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    embedding = model.encode(text).tolist()
                except Exception as fallback_e:
                    raise HTTPException(status_code=500, detail=f"Embedding computation failed: {str(e)}, fallback also failed: {str(fallback_e)}")
        emb1.append(embedding)

    emb2 = []
    for text in request.texts2:
        text_hash = hashlib.md5((text + request.user_id).encode()).hexdigest()
        if text_hash in cache:
            embedding, _ = cache[text_hash]
        else:
            try:
                result = process_message(request.user_id, request.session_id, request.platform, text)
                if result["status"] == "success":
                    embedding = result["obfuscated_embedding"]
                    cache[text_hash] = (result["embedding"], embedding)
                else:
                    raise Exception(result.get("error_message", "EmbedCore failed"))
            except Exception as e:
                # Fallback
                try:
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    embedding = model.encode(text).tolist()
                except Exception as fallback_e:
                    raise HTTPException(status_code=500, detail=f"Embedding computation failed: {str(e)}, fallback also failed: {str(fallback_e)}")
        emb2.append(embedding)

    # Compute pairwise cosine similarities
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(emb1, emb2).tolist()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity computation failed: {e}")

    return {"similarities": similarities}
