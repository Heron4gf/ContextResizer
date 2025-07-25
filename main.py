import os
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import StreamingResponse
import httpx
from dotenv import load_dotenv
from resizer import auto_resize

# Load environment variables
load_dotenv()

app = FastAPI(title="ContextResizer Proxy", version="1.0.0")

# Initialize HTTP clients
httpx_client = httpx.AsyncClient()

# Provider configurations
PROVIDER_CONFIGS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY"
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "api_key_env": "ANTHROPIC_API_KEY"
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY"
    }
}

async def proxy_request(provider: str, path: str, request: Request, headers: Dict[str, str]) -> httpx.Response:
    """Proxy a request to the specified AI provider."""
    if provider not in PROVIDER_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    config = PROVIDER_CONFIGS[provider]
    api_key = os.getenv(config["api_key_env"])
    
    if not api_key:
        raise HTTPException(status_code=500, detail=f"API key not configured for provider: {provider}")
    
    # Prepare headers for the upstream request
    upstream_headers = dict(headers)
    
    # Set the appropriate authorization header based on provider
    if provider == "anthropic":
        upstream_headers["x-api-key"] = api_key
        # Anthropic requires this specific header
        upstream_headers["anthropic-version"] = "2023-06-01"
    else:
        upstream_headers["Authorization"] = f"Bearer {api_key}"
    
    # Remove headers that shouldn't be forwarded
    upstream_headers.pop("host", None)
    upstream_headers.pop("content-length", None)
    
    # Build the upstream URL
    url = f"{config['base_url']}/{path.lstrip('/')}"
    
    # Forward the request
    return await httpx_client.request(
        method=request.method,
        url=url,
        headers=upstream_headers,
        content=await request.body()
    )

@app.post("/v1/auto-resize")
async def auto_resize_endpoint(request: Request):
    """Endpoint for auto-resizing context before sending to LLM."""
    try:
        body = await request.json()
        context = body.get("context", "")
        max_tokens = body.get("max_tokens", 1000)
        
        if not context:
            raise HTTPException(status_code=400, detail="Context is required")
        
        resized_context = auto_resize(context, max_tokens)
        return {"resized_context": resized_context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resizing context: {str(e)}")

@app.api_route("/v1/{provider}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_endpoint(provider: str, path: str, request: Request):
    """Generic proxy endpoint for all supported providers."""
    try:
        # Get headers from the original request
        headers = dict(request.headers)
        
        # Get the request body
        body_bytes = await request.body()
        body = json.loads(body_bytes) if body_bytes and request.headers.get("content-type", "").startswith("application/json") else {}
        
        # Check if this is a chat completion request that needs context resizing
        if path.endswith("chat/completions") and "messages" in body:
            # Apply context resizing to the messages
            messages_jsonl = '\n'.join(json.dumps(msg) for msg in body["messages"])
            resized_context = auto_resize(messages_jsonl, 1000)  # Default to 1000 tokens
            resized_messages = [json.loads(line) for line in resized_context.strip().split('\n') if line.strip()]
            body["messages"] = resized_messages
            
            # Convert modified body back to bytes
            modified_body_bytes = json.dumps(body).encode()
            
            # Create a new HTTP request with the modified body
            config = PROVIDER_CONFIGS[provider]
            api_key = os.getenv(config["api_key_env"])
            
            if not api_key:
                raise HTTPException(status_code=500, detail=f"API key not configured for provider: {provider}")
            
            # Prepare headers for the upstream request
            upstream_headers = dict(headers)
            
            # Set the appropriate authorization header based on provider
            if provider == "anthropic":
                upstream_headers["x-api-key"] = api_key
                # Anthropic requires this specific header
                upstream_headers["anthropic-version"] = "2023-06-01"
            else:
                upstream_headers["Authorization"] = f"Bearer {api_key}"
            
            # Set content type header
            upstream_headers["Content-Type"] = "application/json"
            
            # Remove headers that shouldn't be forwarded
            upstream_headers.pop("host", None)
            upstream_headers.pop("content-length", None)
            upstream_headers.pop("Content-Length", None)
            
            # Set the correct Content-Length header
            upstream_headers["Content-Length"] = str(len(modified_body_bytes))
            
            # Build the upstream URL
            url = f"{config['base_url']}/{path.lstrip('/')}"
            
            # Forward the request
            response = await httpx_client.request(
                method=request.method,
                url=url,
                headers=upstream_headers,
                content=modified_body_bytes
            )
        else:
            # Proxy the request to the specified provider without modification
            response = await proxy_request(provider, path, request, headers)
        
        # Return the response
        return StreamingResponse(
            response.aiter_bytes(),
            status_code=response.status_code,
            headers={
                key: value for key, value in response.headers.items()
                if key.lower() not in ['content-encoding', 'transfer-encoding']
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
