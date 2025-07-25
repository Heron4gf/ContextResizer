# ContextResizer Proxy

A reverse proxy built with FastAPI that enables context resizing for LLM API calls, preserving accuracy while minimizing the context sent to models from providers like OpenAI, Anthropic, and OpenRouter.

## Features

- Auto-resize context before sending to LLMs
- Support multiple providers
- Streaming response support
- Full compatibility with OpenAI client library

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables in a `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Usage

Start the proxy server:
```bash
python main.py
```

The server will start on `http://localhost:8000`.

### Auto-resize endpoint

To resize context before sending to an LLM:

```bash
curl -X POST http://localhost:8000/v1/auto-resize \
  -H "Content-Type: application/json" \
  -d '{
    "context": "{\"role\": \"user\", \"content\": \"Hello\"}\n{\"role\": \"assistant\", \"content\": \"Hi there!\"}",
    "max_tokens": 1000
  }'
```

### Proxy endpoints

To proxy requests to AI providers:

```bash
# OpenAI
curl -X POST http://localhost:8000/v1/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Anthropic
curl -X POST http://localhost:8000/v1/anthropic/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-2",
    "max_tokens": 1000,
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# OpenRouter
curl -X POST http://localhost:8000/v1/openrouter/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## How it works

1. **Context Resizing**: The `auto_resize` function analyzes the conversation context and reduces its size while preserving important information. It uses semantic ordering to determine which messages are most relevant to the latest query and allocates more tokens to those messages.

2. **Proxy Functionality**: The proxy routes requests to the appropriate AI provider, handling authentication and header management automatically.

3. **Semantic Ordering**: Uses ChromaDB to create embeddings of the context messages and orders them by relevance to the latest query.

4. **Summarization**: Uses OpenAI's GPT models to summarize messages when needed to fit within token limits.

## API Endpoints

- `POST /v1/auto-resize` - Resize context before sending to LLM
- `POST /v1/{provider}/{path}` - Proxy requests to AI providers
- `GET /health` - Health check endpoint

## Supported Providers

- OpenAI (`openai`)
- Anthropic (`anthropic`)
- OpenRouter (`openrouter`)

## Configuration

The proxy can be configured using environment variables:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | API key for OpenAI |

## OpenAI Client Compatibility

ContextResizer is fully compatible with the OpenAI Python client library, just like Helicone and other reverse proxies. You can use it as a drop-in replacement for the OpenAI API by simply changing the `base_url` parameter.

### Basic Usage

```python
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

# Configure OpenAI client to use ContextResizer proxy
client = OpenAI(
    api_key=openai_api_key,
    base_url="http://localhost:8000/v1/openai"  # Point to ContextResizer proxy
)

# Use the client exactly as you would with the OpenAI API
response = client.chat.completions.create(
    model="gpt-4.1-nano",
    messages=[
        {"role": "user", "content": "Hello! This is a test message."}
    ],
    max_tokens=50
)

print(response.choices[0].message.content)
```

### HTTP API Usage (Direct requests)

If you prefer to use HTTP requests directly:

```python
import httpx
import asyncio

async def make_request():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/v1/openai/chat/completions",
            json={
                "model": "gpt-4.1-nano",
                "messages": [{"role": "user", "content": "Hello!"}],
                "max_tokens": 50
            },
            headers={"Content-Type": "application/json"}
        )
        return response.json()

# Usage
result = asyncio.run(make_request())
print(result['choices'][0]['message']['content'])
```

### Supported Endpoints

The proxy supports all standard OpenAI API endpoints:

- **Chat Completions**: `POST /v1/openai/chat/completions`
- **Completions**: `POST /v1/openai/completions`
- **Embeddings**: `POST /v1/openai/embeddings`
- **Models**: `GET /v1/openai/models`

The ContextResizer proxy maintains full compatibility with the OpenAI API interface while providing context resizing capabilities to reduce token usage and costs.