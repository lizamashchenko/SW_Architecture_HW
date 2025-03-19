from fastapi import FastAPI, HTTPException
import httpx

class LoggingController:
    def __init__(self, service_instances: list):
        self.service_instances = service_instances

    async def log_message(self, data: dict):
        instance_url = data.get("logger")
        if instance_url not in self.service_instances:
            raise HTTPException(status_code=400, detail="Invalid logger instance")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{instance_url}/log", json=data)
                response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Logging service unavailable: {e}")

    async def get_logs(self):
        return {"status": "Use the Facade Service to retrieve logs"}

app = FastAPI()
logging_controller = LoggingController([
    "http://localhost:8003",
    "http://localhost:8004",
    "http://localhost:8005",
])

@app.post("/log")
async def log_message(data: dict):
    return await logging_controller.log_message(data)

@app.get("/logs")
async def get_logs():
    return await logging_controller.get_logs()
