from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import uuid
import random

class Message(BaseModel):
    msg: str

class FacadeService:
    def __init__(self, config_service_url: str):
        self.config_service_url = config_service_url
        self.logging_service_instances = []
        self.messages_service_url = None

    async def fetch_service_addresses(self):
        async with httpx.AsyncClient(timeout=2.0) as client:
            try:
                response = await client.get(f"{self.config_service_url}/services")
                if response.status_code == 200:
                    config = response.json()
                    self.logging_service_instances = config.get("logging_services", [])
                    self.messages_service_url = config.get("messages_service")
                    return True
            except (httpx.RequestError, httpx.TimeoutException):
                print("Config Service is unavailable")
        return False

    async def send_message(self, msg: str):
        if not self.logging_service_instances or not self.messages_service_url:
            if not await self.fetch_service_addresses():
                return {"status": "Failed", "error": "Could not fetch service addresses"}

        message_id = str(uuid.uuid4())
        random.shuffle(self.logging_service_instances)

        async with httpx.AsyncClient(timeout=2.0) as client:
            for logger_url in self.logging_service_instances:
                try:
                    health_response = await client.get(f"{logger_url}/health")
                    if health_response.status_code == 200:
                        await client.post(f"{logger_url}/log", json={"id": message_id, "msg": msg})
                        return {"status": "Message sent", "id": message_id, "logger": logger_url}
                except (httpx.RequestError, httpx.TimeoutException):
                    print(f"Logger {logger_url} is unavailable, trying another one...")

        return {"status": "Failed", "error": "No available loggers"}

    async def get_messages(self):
        if not self.logging_service_instances or not self.messages_service_url:
            if not await self.fetch_service_addresses():
                return {"status": "Failed", "error": "Could not fetch service addresses"}

        random.shuffle(self.logging_service_instances)

        async with httpx.AsyncClient(timeout=2.0) as client:
            for logger_url in self.logging_service_instances:
                try:
                    health_response = await client.get(f"{logger_url}/health")
                    if health_response.status_code == 200:
                        log_response = await client.get(f"{logger_url}/logs")
                        msg_response = await client.get(f"{self.messages_service_url}/message")
                        return {
                            "logs": log_response.json(),
                            "message_service": msg_response.json(),
                            "logger": logger_url
                        }
                except (httpx.RequestError, httpx.TimeoutException):
                    print(f"Logger {logger_url} is unavailable, trying another one...")

        return {"status": "Failed", "error": "No available loggers"}

app = FastAPI()

facade_service = FacadeService(config_service_url="http://localhost:8001")  # Config Service URL

@app.on_event("startup")
async def startup_event():
    await facade_service.fetch_service_addresses()  # Fetch addresses on startup

@app.post("/send")
async def send_message(message: Message):
    return await facade_service.send_message(message.msg)

@app.get("/messages")
async def get_messages():
    return await facade_service.get_messages()
