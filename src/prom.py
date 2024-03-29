import logging

import httpx
from decouple import config

PROMETHEUS_URL = config("PROMETHEUS_URL", "localhost")
PROMETHEUS_PORT = config("PROMETHEUS_PORT", "9090")

PROM_URL = f"http://{PROMETHEUS_URL}:{PROMETHEUS_PORT}/api/v1/"


class PrometheusException(Exception):
    pass


logger = logging.getLogger(__name__)


async def fetch(query: str, timeout=20.0) -> dict:
    url = PROM_URL + query
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            reply = await client.get(url)
    except httpx.RequestError as exc:
        raise PrometheusException(
            "Unable to contact the Prometheus server", exc
        ) from exc

    if reply.status_code != 200:
        logger.error(f"Invalid status code {reply.status_code}")
        logger.error(reply.content)
        raise PrometheusException("Unexpected error with the metric server")

    json_reply = reply.json()

    status = json_reply["status"]
    if status != "success":
        logger.error(f"Invalid status {status} in Prometheus reply")
        logger.error(reply.content)
        raise PrometheusException("Unexpected status of the metric server")

    return json_reply["data"]["result"]
