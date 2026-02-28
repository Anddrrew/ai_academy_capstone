## Services

| Name | Port | URL | Runtime |
|------|------|-----|---------|
| WebUI | 3000 | http://localhost:3000 | Docker |
| Chat API | 3001 | http://localhost:3001/docs | Python |
| Indexer | 3002 | http://localhost:3002/docs | Python |
| Embedder | 3003 | http://localhost:3003/docs | Python |
| Qdrant | 6333 | http://localhost:6333/dashboard | Docker |

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
# Start Qdrant + WebUI
docker compose up -d

# Start Python services
python start.py
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
