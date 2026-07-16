from langchain_core.tools import tool
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone
from backend.config import settings

_store = None
_embeddings = None

def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    return _embeddings

def _get_store():
    global _store
    if _store is None:
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        _store = PineconeVectorStore(
            index=pc.Index(settings.PINECONE_INDEX),
            embedding=_get_embeddings(),
            namespace=settings.PINECONE_NAMESPACE,
            text_key="text",
        )
    return _store

@tool
def search_stock_knowledge(query: str) -> str:
    """
    Search the stock market knowledge base for information about stock markets,
    investing concepts, financial instruments, market analysis, trading strategies,
    and stock market fundamentals from the uploaded PDF document.
    Use this when the user asks about stock market concepts, investing strategies,
    financial terms, or market analysis techniques.
    """
    try:
        store = _get_store()
        docs = store.similarity_search(query, k=5)

        if not docs:
            return "No relevant information found in the stock market knowledge base for your query."

        output = [f"**Stock Market Knowledge Base Results for:** {query}\n"]
        for i, doc in enumerate(docs, 1):
            text = doc.page_content[:400]
            page = doc.metadata.get("page", "N/A")
            output.append(f"{i}. (Page {page})\n{text}...")

        return "\n\n".join(output)

    except Exception as e:
        return f"Knowledge base search error: {str(e)}"
