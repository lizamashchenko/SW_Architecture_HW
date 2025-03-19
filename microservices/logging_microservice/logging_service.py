from fastapi import FastAPI
import hazelcast
from typing import Dict
import sys

class LoggingService:
    def __init__(self):
        self.hz_client = hazelcast.HazelcastClient(
            cluster_name="haz-cluster",
        )

        self.logs_map = self.hz_client.get_map("logs")

    async def log_message(self, data: Dict[str, str]):
        self.logs_map.put(data["id"], data["msg"]).result()
        print(f"Logged: {data['msg']}")
        return {"status": "Logged"}

    async def get_logs(self):
        logs_future = self.logs_map.entry_set()
        logs = logs_future.result()
        return [{k: v} for k, v in logs]    
    
    def shutdown(self):
        self.hz_client.shutdown()
        print("Hazelcast client shutdown")

app = FastAPI()
logging_service = LoggingService()

@app.post("/log")
async def log_message(data: Dict[str, str]):
    return await logging_service.log_message(data)

@app.get("/logs")
async def get_logs():
    return await logging_service.get_logs()

@app.on_event("shutdown")
async def shutdown():
    logging_service.shutdown()
    print("Logging Service shutdown")

@app.get("/health")
async def health_check():
    return {"status": "OK"}