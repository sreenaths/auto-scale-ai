from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import time, os

app = FastAPI()
START_TIME = time.time()

class Echo(BaseModel):
    msg: str

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/cpu-intensive")
async def cpu_intensive(sleep_seconds: float = 2.0):
    """Sleep-based endpoint for testing auto-scaling"""
    await asyncio.sleep(sleep_seconds)
    return {"sleep_seconds": sleep_seconds}

@app.get("/agent1")
async def agent1():
    pass

@app.get("/agent2")
async def agent2():
    pass

@app.get("/agent3")
async def agent3():
    pass
