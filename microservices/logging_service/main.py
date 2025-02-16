from fastapi import FastAPI
from typing import Dict

app = FastAPI()
logs: Dict[str, str] = {}

@app.post("/log")
async def log_message(data: Dict[str, str]):
    logs[data["id"]] = data["msg"]
    print(f"Logged: {data['msg']}")
    return {"status": "Logged"}

@app.get("/logs")
async def get_logs():
    return list(logs.values())
