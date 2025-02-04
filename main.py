from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import faiss
import json
import os
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers import AutoModelForCausalLM, AutoTokenizer
from sklearn.metrics.pairwise import cosine_similarity
class HybridRetriever:
    def __init__(self, embedding_model: str = "sentence-transformers/all-mpnet-base-v2"):
        es_host = os.getenv('ES_HOST', 'http://localhost:9200')
        es_user = os.getenv('ES_USER', 'elastic')
        es_password = os.getenv('ES_PASSWORD', 'elastic')
        
        self.es = Elasticsearch(
            es_host,
            basic_auth=(es_user, es_password)
        )
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.embedding_dim)

    def load_indexes(self, path: str):
        self.index = faiss.read_index(f"{path}/fifa_laws.faiss")
        with open(f"{path}/document_store.json", 'r') as f:
            self.document_store = json.load(f)

    def elasticsearch_search(self, query: str, top_k: int = 5) -> List[Dict]:
        try:
            response = self.es.search(
                index="fifa_laws",
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["content", "title"],
                            "type": "best_fields",
                            "tie_breaker": 0.3,
                            "minimum_should_match": "80%"
                        }
                    },
                    "size": top_k
                }
            )
        except Exception as e:
            print(f"Elasticsearch search error: {e}")
            raise

        results = []
        for hit in response['hits']['hits']:
            results.append({
                "title": hit["_source"]["title"],
                "content": hit["_source"]["content"],
                "score": hit["_score"]
            })
        return results

    def faiss_search(self, query: str, top_k: int = 5) -> List[Dict]:
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)
        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            result = self.document_store[idx]
            result["score"] = float(dist)
            results.append(result)
        return results

    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict]:
        es_results = self.elasticsearch_search(query, top_k * 2)
        faiss_results = self.faiss_search(query, top_k * 2)

        max_es_score = max([res["score"] for res in es_results], default=1)
        max_faiss_score = max([res["score"] for res in faiss_results], default=1)

        for res in es_results:
            res["score"] /= max_es_score
        for res in faiss_results:
            res["score"] /= max_faiss_score

        combined_results = es_results + faiss_results
        combined_results = sorted(combined_results, key=lambda x: x["score"], reverse=True)

        return combined_results[:top_k]

class ImprovedRAGPipeline:
    def __init__(self, 
                 embedding_model: str = "sentence-transformers/all-mpnet-base-v2",
                 index_path: str = "./indexes"):
        self.retriever = HybridRetriever(embedding_model=embedding_model)
        self.retriever.load_indexes(index_path)
        
        self.tokenizer = AutoTokenizer.from_pretrained("/app/model")
        self.model = AutoModelForCausalLM.from_pretrained("/app/model")
        
        self.embedding_model = SentenceTransformer(embedding_model)

    def generate_response(self, question: str) -> Dict:
        search_results = self.retriever.hybrid_search(question, top_k=2)
        
        context_parts = [result["content"] for result in search_results]
        formatted_context = "\n\n".join(context_parts)
        truncated_context = formatted_context[:4000]
        
        prompt = f"""Below is a question about FIFA laws and regulations, along with relevant context. 
Please provide a clear, accurate answer based solely on the provided context.

Context:
{truncated_context}

Question: {question}

Answer (be concise and specific, list the sanctions and composition details):"""
        
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.2,
            num_beams=5,
            length_penalty=1.1,
            do_sample=True,
            num_return_sequences=1,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        answer = answer.split("Answer (be concise and specific, list the sanctions and composition details):")[-1].strip()
        
        confidence = self.calculate_enhanced_confidence(question, answer, truncated_context)
        
        return {
            "answer": answer,
            "context": truncated_context,
            "sources": search_results,
            "confidence": confidence
        }

    def calculate_enhanced_confidence(self, question: str, answer: str, context: str) -> float:
        question_embedding = self.embedding_model.encode(question, normalize_embeddings=True)
        answer_embedding = self.embedding_model.encode(answer, normalize_embeddings=True)
        context_embedding = self.embedding_model.encode(context, normalize_embeddings=True)
        
        question_answer_similarity = cosine_similarity([question_embedding], [answer_embedding])[0][0]
        answer_context_similarity = cosine_similarity([answer_embedding], [context_embedding])[0][0]
        
        confidence = (0.4 * question_answer_similarity + 0.6 * answer_context_similarity)
        return float(confidence)

app = FastAPI(title="FIFA Law Consultation API")
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
index_path = os.getenv('INDEX_PATH', './indexes_with_overlap_100_chunks_500')
rag_pipeline = ImprovedRAGPipeline(index_path=index_path)

class Query(BaseModel):
    question: str

class Source(BaseModel):
    title: str
    content: str
    relevance_score: float
    chunk_id: str

class Response(BaseModel):
    answer: str
    confidence: float
    sources: List[Source]
    context: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Welcome to the FIFA Law Consultation API"}
@app.get("/health")
async def health_check():
    return {"status": "ok"}
@app.post("/api/chat", response_model=Response)
async def chat_endpoint(query: Query):
    try:
        result = rag_pipeline.generate_response(query.question)
        
        sources = [
            Source(
                title=source["title"],
                content=source["content"],
                relevance_score=source["score"],
                chunk_id=source.get("chunk_id", "")
            ) for source in result.get("sources", [])
        ]
        
        return Response(
            answer=result["answer"],
            confidence=result["confidence"],
            sources=sources,
            context=result["context"] if result["confidence"] > 0.5 else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_endpoint(query: Query):
    try:
        retriever = rag_pipeline.retriever
        results = retriever.hybrid_search(query.question)
        
        sources = [
            Source(
                title=source["title"],
                content=source["content"],
                relevance_score=source["score"],
                chunk_id=source.get("chunk_id", "")
            ) for source in results
        ]
        
        return {"results": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # uvicorn.run(app, host="0.0.0.0", port=int(os.getenv('PORT', '8000')))'
    print("ok")
    uvicorn.run(app, host="0.0.0.0", port=8000)
    print("ok1")