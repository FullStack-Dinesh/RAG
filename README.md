# RAG

# Document AI Assistant
  
  A full-stack AI assistant that lets users upload PDF documents and ask questions about them using Azure OpenAI (Chat + Embedding), Pinecone (Vector Search), FastAPI (Backend), and React (Frontend).

# Features

- Upload and process PDF documents
- Store semantic chunks in Pinecone vector store
- Query using natural language
- Get answers based on document context
- Chat UI with session persistence

# Tech Stack

- Frontend: React + Axios
- Backend: FastAPI (Python)
- Vector DB: Pinecone (Serverless)
- LLM API: Azure OpenAI (Embeddings + GPT Chat)

# Setup Instructions

## 1. Clone the Repository

In terminal/bash

- git clone git clone https://github.com/FullStack-Dinesh/RAG.git
- cd RAG

## 2. Backend Setup (FastAPI)

- cd server
- python -m venv venv                     ---- Create virtualenv
- source venv/bin/activate                ---- Activate
- pip install -r requirements.txt         ---- Packages Installation

- Create .env file:

  AZURE_OPENAI_API_KEY="DJMn0K9PKpOLBqo6PvtKXXCoRCE7F2Ej63Nh1C7IFOFCcvNBe2jvJQQJ99BGACHYHv6XJ3w3AAABACOG6NE0"
  AZURE_OPENAI_ENDPOINT="https://rag-assist-ai.openai.azure.com/"
  AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-35-turbo"
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-3-small"
  AZURE_OPENAI_API_VERSION="2024-12-01-preview"
  PINECONE_API_KEY="pcsk_3Nm2sS_LwF2cN4XEEDtZAi53WG3CtFTCU9VXyX2Cpx9r2KTnga6VTdcdGWdKoGEWPWGu1g"
  PINECONE_ENV="us-east-1"
  PINECONE_INDEX_NAME="rag-index"

- Run FastAPI:

  python -m uvicorn main:app --reload

## 3. Frontend Setup (React)

- cd client
- npm install
- npm install axios
- npm start

# Upload & Ask Flow

1. Upload a .pdf file

2. Chunks are embedded and stored in Pinecone with a session ID

3. User submits a question

4. Embedding of question → vector search in Pinecone → answer using GPT

# Reset Session Feature

- The assistant supports resetting a session to clear uploaded documents and chat history
- Just refresh for further process

# Demo Screenshot

![Chat Demo](screenshot/RAG_DEMO.png)
