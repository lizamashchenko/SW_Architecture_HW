from fastapi import FastAPI
import json

app = FastAPI()

with open("config.json", "r") as f:
    config = json.load(f)

@app.get("/services")
async def get_services():
    return config
