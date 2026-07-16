from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.sqlite_db import init_db
from backend.database.mongo_db import close_client
from backend.auth.router import router as auth_router
from backend.routers.chat import router as chat_router

# Import models so SQLAlchemy knows about them before create_all
from backend.models import user  # noqa: F401
from backend.models.chat_message import ChatMessage  # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize SQLite tables
    await init_db()
    yield
    # Shutdown: close MongoDB connection
    await close_client()

app = FastAPI(
    title="AI Chatbot API",
    description="Multi-tool AI chatbot powered by LangGraph, Groq, and Pinecone",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "AI Chatbot API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
