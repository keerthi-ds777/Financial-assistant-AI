from langchain_core.tools import tool
from tavily import TavilyClient
from backend.config import settings

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    return _client

@tool
def web_search(query: str) -> str:
    """
    Search the web for current news, events, or any information not in your training data.
    Use this for questions about recent events, latest news, current prices not on stock exchanges,
    company news, or any real-world facts that need up-to-date information.
    """
    try:
        client = _get_client()
        response = client.search(query=query, max_results=5, search_depth="advanced")

        results = response.get("results", [])
        if not results:
            return "No results found for this query."

        output = [f"**Web Search Results for:** {query}\n"]
        for i, r in enumerate(results[:5], 1):
            title = r.get("title", "No title")
            url = r.get("url", "")
            content = r.get("content", "")[:300]
            output.append(f"{i}. **{title}**\n   {content}...\n   Source: {url}")

        return "\n\n".join(output)
    except Exception as e:
        return f"Web search error: {str(e)}"
