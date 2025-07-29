import os
from typing import List, Dict, Optional
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
from openai import AzureOpenAI
import tiktoken
import uuid
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from pydantic import BaseModel
from fastapi import Body

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
AZURE_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
AZURE_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-35-turbo")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rag-index")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")

if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, PINECONE_API_KEY]):
    raise EnvironmentError("One or more required environment variables are missing.")

azure_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

pc = Pinecone(api_key=PINECONE_API_KEY)

if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region=PINECONE_REGION
        )
    )
pinecone_index = pc.Index(PINECONE_INDEX_NAME)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
    max_age=600,
)

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class UploadResponse(BaseModel):
    message: str
    session_id: str

class QueryResponse(BaseModel):
    answer: str

class ResetRequest(BaseModel):
    session_id: str    

def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])

def chunk_text(text: str, chunk_size: int = 512) -> List[str]:
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)
    return [tokenizer.decode(tokens[i:i + chunk_size]) for i in range(0, len(tokens), chunk_size)]

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    response = azure_client.embeddings.create(
        input=texts,
        model=AZURE_EMBEDDING_DEPLOYMENT
    )
    return [np.array(embedding.embedding).tolist() for embedding in response.data]

def upsert_documents(documents: List[Dict], namespace: str):
    pinecone_index.upsert(vectors=documents, namespace=namespace)

def query_vector_store(vector: List[float], namespace: Optional[str] = None, top_k: int = 3):
    params = {"vector": vector, "top_k": top_k, "include_metadata": True}
    if namespace:
        params["namespace"] = namespace
    return pinecone_index.query(**params)

RAG_PROMPT_TEMPLATE = """
You are an expert AI assistant trained to provide accurate, step-by-step answers based strictly on the provided context.

Please follow these rules:

1. Use only the provided context to construct your response.
2. If the context does not contain information relevant to the user's question, respond with:
   "This question is not relevant to the uploaded document."

3. Encourage Clarity:
   - Begin your answer with a clear heading summarizing the topic.
   - If any part of the context is ambiguous, acknowledge assumptions made.
   - Maintain a formal, professional tone in all responses.

4. Format your answer in this structured way:
   - Heading (bold)
   - Roman numerals for main ideas
   - Bulleted subpoints (if needed)

Context:
{context}

User's Question:
{question}

Now begin your answer by reasoning step-by-step.
"""

def generate_response(question: str, context: List[str]) -> str:
    formatted_context = "\n".join([f"- {c}" for c in context])
    response = azure_client.chat.completions.create(
        model=AZURE_CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": RAG_PROMPT_TEMPLATE.format(
                question=question,
                context=formatted_context
            )}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

@app.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    session_id = str(uuid.uuid4())
    all_chunks = []
    all_embeddings = []

    try:
        for file in files:
            if not file.filename.endswith(".pdf"):
                raise HTTPException(400, f"Unsupported file: {file.filename}")
            
            temp_path = f"temp_{uuid.uuid4()}.pdf"
            with open(temp_path, "wb") as f:
                f.write(await file.read())
            
            text = extract_text_from_pdf(temp_path)
            chunks = chunk_text(text)
            embeddings = generate_embeddings(chunks)

            all_chunks.extend([
                {
                    "id": str(uuid.uuid4()),
                    "values": emb,
                    "metadata": {"text": chunk, "filename": file.filename}
                } for chunk, emb in zip(chunks, embeddings)
            ])

            os.remove(temp_path)

        upsert_documents(all_chunks, session_id)

        return UploadResponse(
            message=f"Processed {len(all_chunks)} chunks from {len(files)} file(s)",
            session_id=session_id
        )

    except Exception as e:
        raise HTTPException(500, f"Error processing files: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        print("Session ID:", request.session_id)
        embedding = generate_embeddings([request.question])[0]
        results = query_vector_store(embedding, request.session_id)
        context = [match.metadata["text"] for match in results.matches]
        answer = generate_response(request.question, context)
        return QueryResponse(answer=answer)
    except Exception as e:
        print(f"Query error: {e}")
        raise HTTPException(500, f"Error: {str(e)}")

@app.post("/reset")
async def reset_session(request: ResetRequest = Body(...)):
    try:
        if request.session_id:
            pinecone_index.delete(delete_all=True, namespace=request.session_id)
            return {"message": "Session reset successfully"}
        else:
            raise HTTPException(status_code=400, detail="Missing session_id")
    except Exception as e:
        print(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset session")

    
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
