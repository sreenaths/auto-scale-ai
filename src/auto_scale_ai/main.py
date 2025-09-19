from fastapi import FastAPI, Request
from pydantic import BaseModel
import asyncio
import time, os

from auto_scale_ai.server import MCPServer

app = FastAPI()
START_TIME = time.time()

class Echo(BaseModel):
    msg: str

@app.get("/health")
async def health():
    return {"status": "ok"}

mcp_server = MCPServer()

@app.post("/agent")
async def agent(request: Request):
    request_data = await request.json()
    method = request_data['method']
    params = request_data['params']
    bearer_token = request.headers.get('Authorization')

    result = mcp_server.handle_request(method, request_data, bearer_token)

    # Send successful response
    return {
        "jsonrpc": "2.0",
        "id": request_data.get("id"),
        "result": result
    }
