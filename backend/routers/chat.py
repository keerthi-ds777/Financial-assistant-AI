from fastapi import APIRouter, Depends, HTTPException
from backend.auth.dependencies import get_current_user
from backend.models.user import User
from backend.models.schemas import ChatRequest, ChatResponse, SessionHistoryOut, MessageOut
from backend.database.mongo_db import save_message, get_session_history, get_user_sessions
from backend.agent.graph import get_graph
from langchain_core.messages import HumanMessage, AIMessage
import uuid

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Send a message and get a response from the AI agent."""
    session_id = body.session_id or str(uuid.uuid4())
    user_message = body.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Load existing history from MongoDB and convert to LangChain messages
    history = await get_session_history(session_id)
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    # Add the new user message
    messages.append(HumanMessage(content=user_message))

    # Run the LangGraph agent
    graph = get_graph()
    state = {
        "messages": messages,
        "session_id": session_id,
        "user_id": current_user.id,
    }

    result = await graph.ainvoke(state)

    # Extract the last AI message
    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
    reply = ai_messages[-1].content if ai_messages else "I could not generate a response."

    # Persist both messages to MongoDB
    await save_message(session_id, current_user.id, "user", user_message)
    await save_message(session_id, current_user.id, "assistant", reply)

    return ChatResponse(reply=reply, session_id=session_id)


@router.get("/history/{session_id}", response_model=SessionHistoryOut)
async def get_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the full conversation history for a session."""
    messages = await get_session_history(session_id)
    return SessionHistoryOut(
        session_id=session_id,
        messages=[MessageOut(**m) for m in messages],
    )


@router.get("/sessions")
async def get_sessions(current_user: User = Depends(get_current_user)):
    """Get all sessions for the current user."""
    sessions = await get_user_sessions(current_user.id)
    result = []
    for s in sessions:
        last_msg = s.get("messages", [{}])[-1]
        result.append({
            "session_id": s["session_id"],
            "created_at": str(s.get("created_at", "")),
            "updated_at": str(s.get("updated_at", "")),
            "last_message": last_msg.get("content", "")[:80],
        })
    return result


@router.post("/sessions/new")
async def new_session(current_user: User = Depends(get_current_user)):
    """Generate a new session ID."""
    return {"session_id": str(uuid.uuid4())}
