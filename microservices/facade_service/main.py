from fastapi import FastAPI
import httpx
import uuid

app = FastAPI()

LOGGING_SERVICE_URL = "http://localhost:8001"
MESSAGES_SERVICE_URL = "http://localhost:8002"

@app.post("/send")
async def send_message(msg: str):
    message_id = str(uuid.uuid4())
    async with httpx.AsyncClient() as client:
        await client.post(f"{LOGGING_SERVICE_URL}/log", json={"id": message_id, "msg": msg})
    return {"status": "Message sent", "id": message_id}

@app.get("/messages")
async def get_messages():
    async with httpx.AsyncClient() as client:
        log_response = await client.get(f"{LOGGING_SERVICE_URL}/logs")
        msg_response = await client.get(f"{MESSAGES_SERVICE_URL}/message")
    
    return {"logs": log_response.json(), "message_service": msg_response.json()}
