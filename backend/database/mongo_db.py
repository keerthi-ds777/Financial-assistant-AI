from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings
from datetime import datetime, timezone
from typing import Optional

_client: Optional[AsyncIOMotorClient] = None

def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=2000,  # fail fast → 2s instead of 30s
            connectTimeoutMS=2000,
        )
    return _client

def get_db():
    return get_client()[settings.MONGODB_DB]

async def close_client():
    global _client
    if _client:
        _client.close()
        _client = None

# ─── Chat History Helpers ───────────────────────────────────────────────────

async def save_message(session_id: str, user_id: int, role: str, content: str):
    """Append a message to a session's chat history."""
    try:
        db = get_db()
        await db.chat_sessions.update_one(
            {"session_id": session_id},
            {
                "$setOnInsert": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "created_at": datetime.now(timezone.utc),
                },
                "$push": {
                    "messages": {
                        "role": role,
                        "content": content,
                        "timestamp": datetime.now(timezone.utc),
                    }
                },
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            upsert=True,
        )
    except Exception as e:
        print(f"MongoDB save_message failed: {e}. Falling back to SQLite.")
        from backend.database.sqlite_db import AsyncSessionLocal
        from backend.models.chat_message import ChatMessage
        async with AsyncSessionLocal() as session:
            msg = ChatMessage(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
            )
            session.add(msg)
            await session.commit()

async def get_session_history(session_id: str) -> list[dict]:
    """Return the message list for a session."""
    try:
        db = get_db()
        doc = await db.chat_sessions.find_one({"session_id": session_id})
        if doc:
            return doc.get("messages", [])
        return []
    except Exception as e:
        print(f"MongoDB get_session_history failed: {e}. Falling back to SQLite.")
        from backend.database.sqlite_db import AsyncSessionLocal
        from backend.models.chat_message import ChatMessage
        from sqlalchemy import select
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.asc())
            )
            messages = result.scalars().all()
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at,
                }
                for msg in messages
            ]

async def get_user_sessions(user_id: int) -> list[dict]:
    """Return all sessions for a user (newest first)."""
    try:
        db = get_db()
        cursor = db.chat_sessions.find(
            {"user_id": user_id},
            {"session_id": 1, "created_at": 1, "updated_at": 1, "messages": {"$slice": -1}},
        ).sort("updated_at", -1)
        return await cursor.to_list(length=50)
    except Exception as e:
        print(f"MongoDB get_user_sessions failed: {e}. Falling back to SQLite.")
        from backend.database.sqlite_db import AsyncSessionLocal
        from backend.models.chat_message import ChatMessage
        from sqlalchemy import select, func
        async with AsyncSessionLocal() as session:
            stmt = (
                select(
                    ChatMessage.session_id,
                    func.min(ChatMessage.created_at).label("created_at"),
                    func.max(ChatMessage.created_at).label("updated_at")
                )
                .where(ChatMessage.user_id == user_id)
                .group_by(ChatMessage.session_id)
                .order_by(func.max(ChatMessage.created_at).desc())
                .limit(50)
            )
            res = await session.execute(stmt)
            rows = res.all()
            
            sessions_list = []
            for row in rows:
                sid = row[0]
                created_at = row[1]
                updated_at = row[2]
                
                last_msg_stmt = (
                    select(ChatMessage.content)
                    .where(ChatMessage.session_id == sid)
                    .order_by(ChatMessage.created_at.desc())
                    .limit(1)
                )
                last_msg_res = await session.execute(last_msg_stmt)
                last_msg_val = last_msg_res.scalar_one_or_none() or ""
                
                sessions_list.append({
                    "session_id": sid,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "messages": [{"content": last_msg_val}]
                })
            return sessions_list
