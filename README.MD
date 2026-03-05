## Services

| Name            | Port | URL                             | Runtime                |
| --------------- | ---- | ------------------------------- | ---------------------- |
| Chatbot UI/API  | 3001 | http://localhost:3001           | Docker (Next.js)       |
| Knowledge Base  | 3002 | http://localhost:3002/docs      | Python (FastAPI + MCP) |
| Embedder        | 3003 | http://localhost:3003/docs      | Python (FastAPI)       |
| Qdrant          | 6333 | http://localhost:6333/dashboard | Docker                 |
| AI SDK Devtools | 4983 | http://localhost:4983           | Docker                 |

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
# Start Docker services (Qdrant + Chatbot + Devtools)
docker compose up -d

# Start Python services
python3 start.py
```

## Logs

```bash
# Follow all logs
tail -f logs/*.log

# Follow specific service
tail -f logs/knowledge_base.log
```

## Stop

```bash
# Stop Python services (Ctrl+C in the terminal running start.py)

# Stop Docker services
docker compose down
```
