from fastapi import FastAPI
from pydantic import BaseModel
import time, os

app = FastAPI()
START_TIME = time.time()

class Echo(BaseModel):
    msg: str

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/agent1")
async def agent1():
    pass

@app.get("/agent2")
async def agent2():
    pass

@app.get("/agent3")
async def agent3():
    pass
