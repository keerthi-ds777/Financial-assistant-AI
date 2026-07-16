import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    # LLM Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API", "")

    # Tools
    TAVILY_API_KEY: str = os.getenv("TAVILY_API", "")
    CURRENCY_API_KEY: str = os.getenv("CUR_CONVERTER_API", "")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API", "")
    PINECONE_INDEX: str = os.getenv("PINECONE_INDEX", "chat-bot")
    PINECONE_NAMESPACE: str = os.getenv("PINECONE_NAMESPACE", "default")

    # SQLite
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "data/chatbot.db")

    @property
    def sqlite_url(self) -> str:
        # aiosqlite requires three slashes for a relative path
        return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"

    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "chatbot")

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "changeme-secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # GROQ Model — use the tool-use fine-tuned model for reliable function calling
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

settings = Settings()
