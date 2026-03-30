# CrabAI

A single-agent chat system with tool use, similar to Claude's web interface.

## Features

- **Multi-turn chat** with streaming responses (SSE)
- **Tool Use (ReAct)** — agent can chain multiple tools in one conversation turn:
  - `web_search` — search the web via DuckDuckGo
  - `code_execution` — run Python code in a sandboxed environment
  - `memory` — store/retrieve/list persistent memories across conversations
- **File upload** — upload and parse PDF, images, and text/code files
- **Conversation history** — persisted in SQLite, survives restarts
- **Dark theme UI** — clean chat interface with Markdown rendering, code highlighting, and collapsible tool call cards

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + TypeScript + Tailwind CSS 4 + Zustand |
| Backend | Python + FastAPI + SQLAlchemy (async) |
| Database | SQLite (WAL mode) |
| LLM | Anthropic-compatible API (Claude, Kimi K2.5, etc.) |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- An Anthropic-compatible API key

### 1. Clone & configure

```bash
git clone git@github.com:M1chaelWong/CrabAI.git
cd CrabAI
cp .env.example backend/.env
```

Edit `backend/.env`:

```bash
ANTHROPIC_API_KEY=your-api-key

# For Anthropic (default):
# LLM_BASE_URL=
# DEFAULT_MODEL=claude-sonnet-4-20250514

# For Kimi K2.5:
LLM_BASE_URL=https://api.moonshot.cn/anthropic
DEFAULT_MODEL=kimi-k2.5
```

### 2. Start backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi "uvicorn[standard]" anthropic "sqlalchemy[asyncio]" aiosqlite \
    sse-starlette pymupdf pillow httpx python-multipart pydantic-settings python-dotenv aiofiles
uvicorn app.main:app --reload --port 8000
```

### 3. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Architecture

```
User ──► React UI ──► FastAPI (SSE) ──► AgentRunner ──► Claude/Kimi API
                                            │
                                            ├── web_search (DuckDuckGo)
                                            ├── code_execution (subprocess)
                                            └── memory (SQLite)
```

The agent implements a **ReAct loop**: on each turn, it calls the LLM, checks if the response includes tool calls, executes them, feeds results back, and repeats — until the LLM produces a final text response (up to 25 iterations).

## Project Structure

```
backend/
  app/
    main.py              # FastAPI app + lifespan
    config.py            # Pydantic Settings
    agent/
      core.py            # AgentRunner (agentic loop)
      streaming.py       # SSE event constructors
      context.py         # Conversation context builder
    api/
      conversations.py   # Conversation CRUD
      messages.py        # Send message (SSE stream)
      files.py           # File upload/download
    tools/
      registry.py        # Tool registry
      web_search.py      # DuckDuckGo search
      code_execution.py  # Sandboxed Python execution
      memory_tool.py     # Persistent memory
    storage/
      models.py          # SQLAlchemy ORM models
      repositories.py    # Data access layer
    files/
      parser.py          # File parsing (PDF, image, text)

frontend/
  src/
    App.tsx
    hooks/useChat.ts     # SSE stream consumer
    store/chatStore.ts   # Zustand state management
    components/
      chat/              # ChatView, MessageList, ChatInput
      tools/             # ToolCallCard
      markdown/          # MarkdownRenderer
      layout/            # Sidebar, MainLayout
```

## License

MIT
