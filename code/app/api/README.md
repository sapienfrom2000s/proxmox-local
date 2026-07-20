# Flask API

A lightweight Flask API application for the Proxmox Local Homelab platform.

## Endpoints

| Endpoint  | Method | Description                               |
| :-------- | :----- | :---------------------------------------- |
| `/health` | GET    | Health check - returns `{"status": "ok"}` |

## Setup

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running

```bash
python run.py
```

The server starts at `http://127.0.0.1:5000` with debug mode enabled.

## Testing

```bash
curl http://127.0.0.1:5000/health
```

Expected response:

```json
{
  "status": "ok"
}
```
