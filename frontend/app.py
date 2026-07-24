import os
import streamlit as st
import requests
import uuid
from datetime import datetime

# ─── Config ──────────────────────────────────────────────────────────────────

API_BASE = os.getenv("BACKEND_URL", "https://financial-assistant-ai-x1oy.onrender.com")

st.set_page_config(
    page_title="AI Financial Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Styles ──────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        min-height: 100vh;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    /* Main chat area */
    .chat-container {
        max-width: 860px;
        margin: 0 auto;
    }

    /* User bubble */
    .user-bubble {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 6px 0;
        max-width: 75%;
        margin-left: auto;
        box-shadow: 0 4px 15px rgba(102,126,234,0.3);
        font-size: 0.95rem;
        line-height: 1.5;
    }

    /* AI bubble */
    .ai-bubble {
        background: rgba(255,255,255,0.07);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.12);
        color: #e8e8f0;
        padding: 14px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 6px 0;
        max-width: 80%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* Labels */
    .msg-label {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 3px;
        opacity: 0.6;
    }

    .user-label { text-align: right; color: #a78bfa; }
    .ai-label { color: #60a5fa; }

    /* Session card in sidebar */
    .session-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 8px 12px;
        margin: 4px 0;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.82rem;
        color: #c4c4d4;
    }
    .session-card:hover {
        background: rgba(255,255,255,0.1);
        border-color: rgba(102,126,234,0.5);
    }

    /* Input */
    .stTextInput input {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 0.95rem !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(102,126,234,0.5) !important;
    }

    /* Headers */
    h1, h2, h3 { color: white !important; }

    /* Error / success */
    .stAlert { border-radius: 10px !important; }

    /* Hide streamlit branding */
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───────────────────────────────────────────────────────

def init_state():
    defaults = {
        "token": None,
        "user": None,
        "session_id": str(uuid.uuid4()),
        "messages": [],      # list of {"role": "user"|"assistant", "content": str}
        "sessions": [],      # list of past sessions from API
        "page": "login",     # "login" | "register" | "chat"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─── API Helpers ──────────────────────────────────────────────────────────────

def api_post(endpoint: str, data: dict, auth: bool = False) -> tuple[bool, dict]:
    headers = {"Content-Type": "application/json"}
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        resp = requests.post(f"{API_BASE}{endpoint}", json=data, headers=headers, timeout=60)
        if resp.status_code in (200, 201):
            return True, resp.json()
        return False, {"detail": resp.json().get("detail", "Request failed")}
    except requests.exceptions.ConnectionError:
        return False, {"detail": "Cannot connect to backend. Is it running?"}
    except Exception as e:
        return False, {"detail": str(e)}

def api_get(endpoint: str) -> tuple[bool, any]:
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=30)
        if resp.status_code == 200:
            return True, resp.json()
        return False, resp.json()
    except requests.exceptions.ConnectionError:
        return False, {"detail": "Cannot connect to backend"}
    except Exception as e:
        return False, {"detail": str(e)}

def load_sessions():
    ok, data = api_get("/chat/sessions")
    if ok:
        st.session_state.sessions = data

def load_session_history(session_id: str):
    ok, data = api_get(f"/chat/history/{session_id}")
    if ok:
        st.session_state.messages = [
            {"role": m["role"], "content": m["content"]}
            for m in data.get("messages", [])
        ]
        st.session_state.session_id = session_id

# ─── Auth Pages ───────────────────────────────────────────────────────────────

def render_login():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🤖 AI Financial Assistant")
        st.markdown("<p style='color:#a0a0b8; margin-bottom:30px'>Powered by LangGraph · Groq · Pinecone</p>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Sign In", use_container_width=True)

        if submit:
            if not username or not password:
                st.error("Please fill in all fields.")
            else:
                ok, data = api_post("/auth/login", {"username": username, "password": password})
                if ok:
                    st.session_state.token = data["access_token"]
                    st.session_state.user = data["user"]
                    st.session_state.page = "chat"
                    load_sessions()
                    st.rerun()
                else:
                    st.error(data.get("detail", "Login failed"))

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Create an account →", use_container_width=True):
            st.session_state.page = "register"
            st.rerun()

def render_register():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🤖 Create Account")
        st.markdown("<p style='color:#a0a0b8; margin-bottom:30px'>Join the AI Financial Assistant</p>", unsafe_allow_html=True)

        with st.form("register_form"):
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
            submit = st.form_submit_button("Create Account", use_container_width=True)

        if submit:
            if not all([username, email, password, confirm]):
                st.error("Please fill in all fields.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                ok, data = api_post("/auth/register", {
                    "username": username, "email": email, "password": password
                })
                if ok:
                    st.session_state.token = data["access_token"]
                    st.session_state.user = data["user"]
                    st.session_state.page = "chat"
                    st.session_state.sessions = []
                    st.rerun()
                else:
                    st.error(data.get("detail", "Registration failed"))

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Sign In", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

# ─── Chat Page ────────────────────────────────────────────────────────────────

def render_chat():
    user = st.session_state.user or {}

    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {user.get('username', 'User')}")
        st.markdown(f"<small style='color:#888'>{user.get('email','')}</small>", unsafe_allow_html=True)
        st.divider()

        # New chat button
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()

        st.markdown("#### 💬 Recent Sessions")

        # Load sessions if empty
        if not st.session_state.sessions:
            load_sessions()

        for sess in st.session_state.sessions[:15]:
            sid = sess.get("session_id", "")
            preview = sess.get("last_message", "New conversation")[:50]
            updated = sess.get("updated_at", "")[:10]
            label = f"📝 {preview}..." if len(preview) == 50 else f"📝 {preview}"
            if st.button(label, key=f"sess_{sid}", use_container_width=True):
                load_session_history(sid)
                st.rerun()
            st.markdown(f"<small style='color:#666;margin-left:4px'>{updated}</small>", unsafe_allow_html=True)

        st.divider()

        # Capabilities
        st.markdown("#### 🛠️ Capabilities")
        st.markdown("""
        <div style='color:#a0a0b8;font-size:0.82rem;line-height:2'>
        📈 Stock Prices & History<br>
        🌐 Live Web Search<br>
        💱 Currency Conversion<br>
        📚 Stock Market Knowledge<br>
        🧠 Groq LLaMA 3.3 70B
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        if st.button("🚪 Sign Out", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            init_state()
            st.rerun()

    # Main chat area
    st.markdown("### 🤖 AI Financial Assistant")
    st.markdown(f"<small style='color:#888'>Session: {st.session_state.session_id[:8]}...</small>", unsafe_allow_html=True)
    st.markdown("---")

    # Display messages
    messages_container = st.container()
    with messages_container:
        if not st.session_state.messages:
            st.markdown("""
            <div style='text-align:center; padding: 60px 20px; color: #6b6b8a;'>
                <div style='font-size:3rem;margin-bottom:16px'>🤖</div>
                <h3 style='color:#8888aa'>Hello! I'm your AI Financial Assistant</h3>
                <p>Ask me about stocks, currencies, market news, or investing strategies.</p>
                <br>
                <div style='display:flex;gap:12px;justify-content:center;flex-wrap:wrap'>
                    <span style='background:rgba(255,255,255,0.07);padding:8px 16px;border-radius:20px;font-size:0.85rem'>📈 "What is Apple's stock price?"</span>
                    <span style='background:rgba(255,255,255,0.07);padding:8px 16px;border-radius:20px;font-size:0.85rem'>💱 "Convert 100 USD to INR"</span>
                    <span style='background:rgba(255,255,255,0.07);padding:8px 16px;border-radius:20px;font-size:0.85rem'>🌐 "Latest Tesla news"</span>
                    <span style='background:rgba(255,255,255,0.07);padding:8px 16px;border-radius:20px;font-size:0.85rem'>📚 "What is a P/E ratio?"</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"<div class='user-label msg-label'>You</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='user-bubble'>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='ai-label msg-label'>🤖 Assistant</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='ai-bubble'>{msg['content']}</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

    # Input area
    st.markdown("---")
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "Message",
                placeholder="Ask about stocks, currencies, market news...",
                label_visibility="collapsed",
            )
        with col2:
            send = st.form_submit_button("Send ✈️", use_container_width=True)

    if send and user_input.strip():
        # Optimistic UI update
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})

        with st.spinner("🤔 Thinking..."):
            ok, data = api_post(
                "/chat",
                {"message": user_input.strip(), "session_id": st.session_state.session_id},
                auth=True,
            )

        if ok:
            reply = data.get("reply", "No response")
            st.session_state.messages.append({"role": "assistant", "content": reply})
            # Refresh session list
            load_sessions()
        else:
            error_msg = data.get("detail", "Something went wrong. Please try again.")
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ {error_msg}"})

        st.rerun()

# ─── Router ───────────────────────────────────────────────────────────────────

if st.session_state.page == "login":
    render_login()
elif st.session_state.page == "register":
    render_register()
elif st.session_state.page == "chat":
    if not st.session_state.token:
        st.session_state.page = "login"
        st.rerun()
    else:
        render_chat()
