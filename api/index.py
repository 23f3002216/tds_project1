from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
import json

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from vector_search import VectorSearch
from llm_client import LLMClient
from response_formatter import ResponseFormatter

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

# Initialize components
try:
    data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed_data.json')
    vector_search = VectorSearch(data_file)
    llm_client = LLMClient()
    formatter = ResponseFormatter()
except Exception as e:
    print(f"Initialization error: {e}")
    vector_search = None
    llm_client = None
    formatter = None

@app.post("/api/")
async def answer_question(request: QuestionRequest):
    """Main API endpoint for answering questions"""
    try:
        if not all([vector_search, llm_client, formatter]):
            raise HTTPException(status_code=500, detail="Service not properly initialized")
        
        # Search for relevant context
        search_results = vector_search.search(request.question, top_k=10)
        
        if not search_results:
            return {
                "answer": "I don't have enough information to answer this question based on the available course content and discussions.",
                "links": []
            }
        
        # Extract context for LLM
        context = [result[0] for result in search_results]
        
        # Generate answer using LLM
        answer = llm_client.generate_answer(
            request.question, 
            context, 
            request.image
        )
        
        # Format response
        response = formatter.format_response(answer, search_results)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
async def health_check():
    return {"status": "healthy"}

# For Vercel
handler = app