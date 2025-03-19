from fastapi import FastAPI

class MessagesService:
    async def get_message(self):
        return {"message": "Not implemented yet"}

app = FastAPI()
messages_service = MessagesService()

@app.get("/message")
async def get_message():
    return await messages_service.get_message()
