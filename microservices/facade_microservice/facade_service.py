import argparse
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import uuid
import random
import hazelcast
import os, sys

import uvicorn
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.consul_utils import register_service, deregister_service, fetch_instances, get_consul_kv

class Message(BaseModel):
    msg: str

class FacadeService:
    def __init__(self, cluster_name, queue_name, service_name="facade-service"):
        self.hz_client = hazelcast.HazelcastClient(cluster_name=cluster_name)
        self.msg_queue = self.hz_client.get_queue(queue_name)
        self.service_name = service_name
        self.service_id = f"{service_name}-{os.getpid()}"

        self.logging_service_instances = []
        self.messages_service_instances = []

    async def fetch_service_addresses(self):
        logging_instances = await fetch_instances("logging-service")
        message_instances = await fetch_instances("messages-service")

        print(logging_instances)
        print(message_instances)

        if logging_instances and message_instances:
            self.logging_service_instances = logging_instances
            self.messages_service_instances = message_instances
            return True

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

facade_service = None


@app.on_event("startup")
async def startup_event():
    global facade_service
    cluster_name_ = await get_consul_kv("cluster_name")
    queue_name_ = await get_consul_kv("queue_name")
    facade_service = FacadeService(cluster_name=cluster_name_, queue_name = queue_name_)
    port = int(os.environ["APP_PORT"])
    await register_service(facade_service.service_name, facade_service.service_id, "localhost", port)
    await facade_service.fetch_service_addresses()

@app.post("/send")
async def send_message(message: Message):
    return await facade_service.send_message(message.msg)

@app.get("/messages")
async def get_messages():
    return await facade_service.get_messages()

@app.on_event("shutdown")
async def shutdown():
    await deregister_service(facade_service.service_id)
    facade_service.shutdown()
    print("Facade Service shutdown")

@app.get("/health")
async def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    os.environ["APP_PORT"] = str(args.port)

    uvicorn.run("facade_service:app", host="0.0.0.0", port=args.port, reload=False)