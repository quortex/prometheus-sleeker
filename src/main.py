import asyncio
import logging
import signal
import time
from threading import Event

from prometheus_client import start_http_server

from .conf import configure
from .process import Process
from .prom import PrometheusException

METRIC_PORT = 6200
REFRESH_INTERVAL = 5  # seconds
STOP_EVENT = Event()


logger = logging.getLogger(__name__)


def signal_handler(_signal_number, _frame):
    STOP_EVENT.set()


async def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    config = configure()
    start_http_server(port=METRIC_PORT)

    process = Process(config)

    retry_time = 5
    while not STOP_EVENT.is_set():
        try:
            now = time.time()
            await process.load(int(now))
            break
        except PrometheusException as exc:
            logger.error(exc)
            logger.error(f"Retrying in {retry_time} seconds...")
            await asyncio.sleep(retry_time)
            retry_time += 5

    logger.info("Loading done")

    time_target = now + REFRESH_INTERVAL

    wait_time = REFRESH_INTERVAL

    while not STOP_EVENT.wait(timeout=wait_time):
        try:
            await process.tick(int(time_target))
        except PrometheusException as exc:
            logger.error(exc)

        now = time.time()

        overshot = now - time_target
        wait_time = REFRESH_INTERVAL - overshot
        time_target += REFRESH_INTERVAL


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(main())
