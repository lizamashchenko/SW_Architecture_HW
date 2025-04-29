import httpx

async def register_service(service_name, service_id, service_ip, service_port):
    consul_url = "http://localhost:8500/v1/agent/service/register"
    service_payload = {
        "Name": service_name,
        "ID": service_id,
        "Address": service_ip,
        "Port": service_port,
        "Check": {
            "HTTP": f"http://{service_ip}:{service_port}/health",
            "Interval": "10s",
            "Timeout": "5s"
        }
    }
    async with httpx.AsyncClient() as client:
        print("Registering in Consul...")
        response = await client.put(consul_url, json=service_payload)
        response.raise_for_status()
        print(f"Registered service {service_name} in Consul as {service_id}")

async def deregister_service(service_id):
    consul_url = f"http://localhost:8500/v1/agent/service/deregister/{service_id}"
    async with httpx.AsyncClient() as client:
        await client.put(consul_url)
        print(f"Deregistered from Consul: {service_id}")

async def fetch_instances(service_name: str, timeout: float = 2.0):
    url = f"http://localhost:8500/v1/catalog/service/{service_name}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                services = response.json()
                return [
                    f"http://{service['ServiceAddress']}:{service['ServicePort']}"
                    for service in services
                ]
        except (httpx.RequestError, httpx.TimeoutException):
            print(f"Failed to fetch instances for {service_name}")
    return []

async def get_consul_kv(key):
    url = f"http://localhost:8500/v1/kv/{key}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                value = resp.json()[0]["Value"]
                import base64
                return base64.b64decode(value).decode()
        except Exception as e:
            print(f"Failed to fetch {key} from Consul:", e)
    return ""