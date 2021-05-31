import logging

from decouple import config
import httpx

PROMETHEUS_URL = config("PROMETHEUS_URL", "localhost")
PROMETHEUS_PORT = config("PROMETHEUS_PORT", "9090")

PROM_URL = f"http://{PROMETHEUS_URL}:{PROMETHEUS_PORT}/api/v1/"


logger = logging.getLogger(__name__)


async def fetch(query: str,) -> dict:
    url = PROM_URL + query

    async with httpx.AsyncClient() as client:
        reply = await client.get(url)

    if reply.status_code != 200:
        logger.error(f"Invalid status code {reply.status_code}")
        logger.error(reply.content)
        raise Exception("Unexpected error with the metric server")

    json_reply = reply.json()

    status = json_reply["status"]
    if status != "success":
        logger.error(f"Invalid status {status} in Prometheus reply")
        logger.error(reply.content)
        raise Exception("Unexpected status of the metric server")

    return json_reply["data"]["result"]
