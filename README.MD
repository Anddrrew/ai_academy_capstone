# AI Academy Capstone Project: Agentic RAG Assistant

Local multi-service RAG assistant with:

- Next.js chatbot UI and agent orchestration
- FastAPI knowledge base service with MCP tools
- FastAPI embedding service (Qwen3-Embedding-0.6B)
- Qdrant vector database
- Optional GitHub-powered codebase research agent

## Project Structure

```text
.
├── docs/                         # GitHub Pages architecture render
│   ├── index.html
│   └── architecture.mmd
├── knowledge_base/               # Uploaded source files to index
├── logs/                         # Runtime logs per service
├── packages/
│   ├── chatbot/                  # Next.js UI + agent orchestration
│   ├── embedder/                 # FastAPI embedding service
│   ├── knowledge_base/           # FastAPI KB + MCP + indexing worker
│   └── config.py                 # Shared Python config (env-driven)
├── docker-compose.yml            # Docker services (chatbot, qdrant, devtools)
├── pyproject.toml                # Root uv workspace config
├── uv.lock                       # Locked Python dependencies
├── start.py                      # Python service launcher/status dashboard
└── README.MD
```

## Architecture

Live render: https://anddrrew.github.io/ai_academy_capstone/

Source file: [docs/architecture.mmd](./docs/architecture.mmd)

## Local Setup

### Prerequisites

- Docker + Docker Compose
- `uv` (https://docs.astral.sh/uv/#installation)

### Steps

1. Create `.env` from the template and fill required values.

```bash
cp .env.example .env
```

2. Install Python dependencies (workspace).

```bash
uv sync
```

3. Start all services.

```bash
docker compose up -d --build && uv run python start.py
```

When startup is complete, open `http://localhost:3001`.

Service URLs:

- Chatbot UI/API: `http://localhost:3001`
- Knowledge Base: `http://localhost:3002/docs`
- Embedder: `http://localhost:3003/docs`
- Qdrant: `http://localhost:6333/dashboard`
- AI SDK Devtools: `http://localhost:4983`

### Logs

```bash
# all service logs
tail -f logs/*.log

# focused logs
tail -f logs/chatbot.log
tail -f logs/knowledge_base.log
tail -f logs/embedder.log
```

### Stop

```bash
# stop Python services
# (Ctrl+C in the terminal running start.py)

# stop Docker services
docker compose down
```
