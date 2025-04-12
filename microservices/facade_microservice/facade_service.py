from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import uuid
import random
import hazelcast

class Message(BaseModel):
    msg: str

class FacadeService:
    def __init__(self, config_service_url: str):
        self.config_service_url = config_service_url
        self.logging_service_instances = []
        self.messages_service_instances = []
        self.hz_client = hazelcast.HazelcastClient(            
            cluster_name="haz-cluster",
        )
        self.msg_queue = self.hz_client.get_queue("messages-queue")


    async def fetch_service_addresses(self):
        async with httpx.AsyncClient(timeout=2.0) as client:
            try:
                response = await client.get(f"{self.config_service_url}/services")
                if response.status_code == 200:
                    config = response.json()
                    self.logging_service_instances = config.get("logging_services", [])
                    self.messages_service_instances = config.get("messages_services", [])
                    return True
            except (httpx.RequestError, httpx.TimeoutException):
                print("Config Service is unavailable")
        return False

    async def send_message(self, msg: str):
        if not self.logging_service_instances or not self.messages_service_instances:
            if not await self.fetch_service_addresses():
                return {"status": "Failed", "error": "Could not fetch service addresses"}

        message_id = str(uuid.uuid4())
        random.shuffle(self.logging_service_instances)
        sent = False

        async with httpx.AsyncClient(timeout=2.0) as client:
            for logger_url in self.logging_service_instances:
                try:
                    health_response = await client.get(f"{logger_url}/health")
                    if health_response.status_code == 200:
                        await client.post(f"{logger_url}/log", json={"id": message_id, "msg": msg})
                        sent = True
                        break
                except (httpx.RequestError, httpx.TimeoutException):
                    print(f"Logger {logger_url} is unavailable, trying another one...")

        self.msg_queue.put(msg).result()

        if sent:
            return {"status": "Message sent", "ID": message_id, "logger": logger_url}
        else:
            return {"status": "Failed", "error": "Could not reach any logging service"}
            


    async def get_messages(self):
        if not self.logging_service_instances or not self.messages_service_instances:
            if not await self.fetch_service_addresses():
                return {"status": "Failed", "error": "Could not fetch service addresses"}

        random.shuffle(self.logging_service_instances)
        random.shuffle(self.messages_service_instances)

        async with httpx.AsyncClient(timeout=2.0) as client:
            for logger_url in self.logging_service_instances:
                try:
                    health_response = await client.get(f"{logger_url}/health")
                    if health_response.status_code == 200:
                        log_response = await client.get(f"{logger_url}/logs")
                        for msg_url in self.messages_service_instances:
                            try:
                                msg_response = await client.get(f"{msg_url}/message")
                                if msg_response.status_code == 200:
                                    return {
                                        "logs": log_response.json(),
                                        "message_service": msg_response.json(),
                                        "logger": logger_url,
                                        "message_instance": msg_url
                                    }
                            except (httpx.RequestError, httpx.TimeoutException):
                                print(f"Message service {msg_url} unavailable, trying another one...")

                        return {
                            "logs": log_response.json(),
                            "message_service": {"status": "Failed", "error": "No available message services"},
                            "logger": logger_url
                        }
                    
                except (httpx.RequestError, httpx.TimeoutException):
                    print(f"Logger {logger_url} is unavailable, trying another one...")

        return {"status": "Failed", "error": "No available loggers"}
    
    def shutdown(self):
        self.hz_client.shutdown()
        print("Hazelcast client shutdown")

app = FastAPI()

facade_service = FacadeService(config_service_url="http://localhost:8001")

@app.on_event("startup")
async def startup_event():
    await facade_service.fetch_service_addresses()

@app.post("/send")
async def send_message(message: Message):
    return await facade_service.send_message(message.msg)

@app.get("/messages")
async def get_messages():
    return await facade_service.get_messages()

@app.on_event("shutdown")
async def shutdown():
    facade_service.shutdown()
    print("Facade Service shutdown")