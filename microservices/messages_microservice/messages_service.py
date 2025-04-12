from fastapi import FastAPI
import hazelcast
import asyncio

import asyncio
import concurrent.futures

class MessagesService:
    def __init__(self):
        self.hz = hazelcast.HazelcastClient(cluster_name="haz-cluster")
        self.msg_queue = self.hz.get_queue("messages-queue")
        self.messages_list = []
        self.executor = concurrent.futures.ThreadPoolExecutor()

    async def poll_messages(self):
        loop = asyncio.get_running_loop()
        while True:
            msg_future = self.msg_queue.take()  # Hazelcast's future
            msg = await loop.run_in_executor(self.executor, msg_future.result)  # ✅ Proper async-compatible blocking
            self.messages_list.append(msg)
            print(f"[{id(self)}] Received message: {msg}")


    async def get_message(self):
        return {"ID": id(self), "messages": self.messages_list}
    
    def shutdown(self):
        self.hz_client.shutdown()
        print("Hazelcast client shutdown")

app = FastAPI()
messages_service = MessagesService()

@app.on_event("shutdown")
async def shutdown():
    messages_service.shutdown()
    print("Messages Service shutdown")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(messages_service.poll_messages())

@app.get("/message")
async def get_message():
    return await messages_service.get_message()
