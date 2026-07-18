# AI Financial Chatbot

A full-stack AI chatbot with LangGraph, Groq, Pinecone RAG, FastAPI backend, and Streamlit frontend.

## 🏗️ Architecture

```
Streamlit (frontend) → FastAPI (backend) → LangGraph Agent
                                           ├── MySQL (auth)
                                           ├── MongoDB (chat history)
                                           └── Tools:
                                               ├── yfinance (stock data)
                                               ├── Tavily (web search)
                                               ├── Currency Converter
                                               └── Pinecone RAG (PDF)
```

## 🔧 Setup

### 1. Install dependencies
```bash
uv pip install -r requirements.txt
```

### 2. Configure `.env`
Update the following in `.env`:
```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=chatbot_auth

MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=chatbot
```

### 3. Ensure sqlite DB exists
```sql
CREATE DATABASE IF NOT EXISTS chatbot_auth;
```

### 4. Seed Pinecone (already done ✅)
```bash
python vector_db.py
```

## 🚀 Running

### Start Backend
```bash
uvicorn backend.main:app --reload --port 8000
```

### Start Frontend (new terminal)
```bash
streamlit run frontend/app.py
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get JWT |
| POST | `/chat` | Send message to agent |
| GET | `/chat/history/{session_id}` | Get session history |
| GET | `/chat/sessions` | List user sessions |
| POST | `/chat/sessions/new` | Create new session |

## 🛠️ Tools Available

| Tool | Description |
|------|-------------|
| `get_stock_price` | Live stock price & info via yfinance |
| `get_stock_history` | Historical stock performance |
| `web_search` | Real-time web search via Tavily |
| `convert_currency` | Currency conversion |
| `get_exchange_rate` | Exchange rate lookup |
| `search_stock_knowledge` | Pinecone RAG over stock market PDF |

## 🔗 Architecture Presentation :

    open /Users/lravi/.gemini/antigravity-ide/brain/f97c2f74-0294-47bb-bab0-d82b4d47b94b/architecture_presentation.html