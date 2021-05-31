import asyncio
import signal
import time
from threading import Event

from prometheus_client import start_http_server

from .conf import configure
from .process import Process

METRIC_PORT = 6200
REFRESH_INTERVAL = 5  # seconds
STOP_EVENT = Event()


def signal_handler(_signal_number, _frame):
    STOP_EVENT.set()


async def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    metrics = configure()
    start_http_server(port=METRIC_PORT)

    process = Process(metrics)

    now = time.time()
    await process.load(int(now))

    time_target = now + REFRESH_INTERVAL

    wait_time = REFRESH_INTERVAL

    await process.tick(time_target)
    while not STOP_EVENT.wait(timeout=wait_time):

        await process.tick(int(time_target))

        now = time.time()

        overshot = now - time_target
        wait_time = REFRESH_INTERVAL - overshot
        time_target += REFRESH_INTERVAL


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(main())
