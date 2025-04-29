import argparse
from fastapi import FastAPI
import hazelcast
import os, sys
import asyncio
import concurrent.futures

import uvicorn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.consul_utils import register_service, deregister_service, get_consul_kv

class MessagesService:
    def __init__(self, cluster_name, queue_name, service_name="messages-service"):
        self.hz = hazelcast.HazelcastClient(cluster_name=cluster_name)
        self.msg_queue = self.hz.get_queue(queue_name)

        self.service_name = service_name
        self.service_id = f"{service_name}-{os.getpid()}"

        self.messages_list = []
        self.executor = concurrent.futures.ThreadPoolExecutor()

    async def poll_messages(self):
        loop = asyncio.get_running_loop()
        while True:
            msg_future = self.msg_queue.take()
            msg = await loop.run_in_executor(self.executor, msg_future.result)
            self.messages_list.append(msg)
            print(f"[{id(self)}] Received message: {msg}")


    async def get_message(self):
        return {"ID": id(self), "messages": self.messages_list}
    
    def shutdown(self):
        self.hz.shutdown()
        print("Hazelcast client shutdown")

app = FastAPI()
messages_service = None

@app.on_event("shutdown")
async def shutdown():
    messages_service.shutdown()
    await deregister_service(messages_service.service_id)
    print("Messages Service shutdown")

@app.on_event("startup")
async def startup_event():
    global messages_service
    cluster_name_ = await get_consul_kv("cluster_name")
    queue_name_ = await get_consul_kv("queue_name")
    messages_service = MessagesService(cluster_name=cluster_name_, queue_name = queue_name_)
    asyncio.create_task(messages_service.poll_messages())
    port = int(os.environ["APP_PORT"])
    await register_service(messages_service.service_name, messages_service.service_id, "localhost", port)

@app.get("/message")
async def get_message():
    return await messages_service.get_message()

@app.get("/health")
async def health_check():
    return {"status": "OK"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    os.environ["APP_PORT"] = str(args.port)

    uvicorn.run("messages_service:app", host="0.0.0.0", port=args.port, reload=False)
