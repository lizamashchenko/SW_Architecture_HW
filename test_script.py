import httpx
import asyncio

async def send_messages():
    async with httpx.AsyncClient(timeout=10.0) as client:  # Increased timeout
        for i in range(1, 11):
            try:
                response = await client.post(
                    "http://localhost:8000/send",  
                    json={"msg": f"msg{i}"}
                )
                print(f"Sent msg{i}: {response.json()}")
            except httpx.RequestError as e:
                print(f"Failed to send msg{i}: {e}")

asyncio.run(send_messages())
