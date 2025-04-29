from fastapi import FastAPI
import hazelcast
from typing import Dict
import os
import sys
import argparse
import uvicorn
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.consul_utils import register_service, deregister_service, get_consul_kv

class LoggingService:
    def __init__(self, cluster_name, map_name, service_name="logging-service"):
        self.hz_client = hazelcast.HazelcastClient(cluster_name=cluster_name)
        self.logs_map = self.hz_client.get_map(map_name)
        self.service_name = service_name
        self.service_id = f"{service_name}-{os.getpid()}"

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
logging_service = None

@app.post("/log")
async def log_message(data: Dict[str, str]):
    return await logging_service.log_message(data)

@app.get("/logs")
async def get_logs():
    return await logging_service.get_logs()

@app.on_event("startup")
async def startup():
    global logging_service
    cluster_name_ = await get_consul_kv("cluster_name")
    map_name_ = await get_consul_kv("map_name")
    logging_service = LoggingService(cluster_name=cluster_name_, map_name=map_name_)
    port = int(os.environ["APP_PORT"])
    await register_service(logging_service.service_name, logging_service.service_id, "localhost", port)

@app.on_event("shutdown")
async def shutdown():
    await deregister_service(logging_service.service_id)
    logging_service.shutdown()

@app.get("/health")
async def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    os.environ["APP_PORT"] = str(args.port)

    uvicorn.run("logging_service:app", host="0.0.0.0", port=args.port, reload=False)
