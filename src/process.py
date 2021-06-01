import asyncio
import logging
from typing import List

from . import prom
from .metric import Metrics

logger = logging.getLogger(__name__)


def pretty_labels(labels):
    """
    Display the labels in a form usable in promql queries
    """
    return "{" + ",".join([f'{key}="{value}"' for key, value in labels.items()]) + "}"


async def load_metric(metric: Metrics, timestamp):
    # Max 11000 points (Prometheus limit), with 5s resolution, we can fetch 15 hours of data
    start = timestamp - 54000  # 15 hours before

    # Get the last available value of the output metric. We are interested in the value, to start our counter at this value,
    # and the timestamp, because we will have to catch up the base counter increments from this time, until now.

    query = (
        "query_range?query="
        + metric.config.get_recatch_query()
        + f"&start={start}&end={timestamp}&step=5s"
    )
    data = await prom.fetch(query)

    # Store the values and timestamp of the output metrics
    recatch_dots_by_key = {}

    for element in data:
        labels = metric.config.filter_labels(element["metric"])
        key = tuple(labels.values())

        last_dot = element["values"][-1]

        # Convert counter value from str to int
        last_dot = last_dot[0], int(last_dot[1])

        logger.debug(
            f"Found dot {last_dot} for {metric.config.name}{pretty_labels(labels)}"
        )
        recatch_dots_by_key[key] = last_dot

    # Fetch the base counters

    query = (
        "query_range?query="
        + metric.config.get_query()
        + f"&start={start}&end={timestamp}&step=5s"
    )
    data = await prom.fetch(query)
    for element in data:
        labels = metric.config.filter_labels(element["metric"])
        key = tuple(labels.values())

        values = element["values"]

        if key in recatch_dots_by_key:

            # Store the last seen base counter
            metric.previous_values_by_key[key] = int(values[-1][1])

            # Remove the current metric from recatch_dots_by_key.
            last_timestamp, counter_value = recatch_dots_by_key.pop(key)

            # Keep only the values seen during the sleeker unavailability
            catchup_values = [[t, v] for [t, v] in values if t >= last_timestamp]

            base_counter_incr = 0
            for i in range(len(catchup_values) - 1):
                tn, vn = catchup_values[i]
                tnp, vnp = catchup_values[i + 1]
                vn, vnp, tn, tnp = int(vn), int(vnp), float(tn), float(tnp)
                increment = vnp - vn if vnp >= vn else vnp
                base_counter_incr += increment

            logger.debug(
                f"Catchup: {counter_value} + {base_counter_incr} for {metric.config.name}{pretty_labels(labels)}"
            )
            metric.counter.labels(**labels).inc(counter_value + base_counter_incr)

    # If the base counter was not found, start the output counter where it was last time it was
    # seen

    for key, dot in recatch_dots_by_key.items():
        _timestamp, counter_value = dot
        labels = metric.config.key_to_label(key)
        logger.warning(
            f"No base counter found for {metric.config.base}{pretty_labels(labels)}, base counter catchup failed."
        )
        metric.counter.labels(**labels).inc(counter_value)


async def tick_metric(metric, timestamp):
    query = "query?query=" + metric.config.get_query() + f"&time={timestamp}"
    data = await prom.fetch(query)
    for element in data:
        labels = metric.config.filter_labels(element["metric"])
        key = tuple(labels.values())

        value = element["value"]

        if not value:
            logger.warning(
                f"No base value for {metric.config.base}{pretty_labels(labels)}"
            )
            continue

        _t, v = value
        v = int(v)

        previous_value = metric.previous_values_by_key.get(key)
        if previous_value:
            incr = v - previous_value
            if incr < 0:
                # Counter has reset
                logger.info(
                    f"Reset found on counter {metric.config.base}{pretty_labels(labels)}"
                )
                incr = v
        else:
            logger.info(
                f"New labels found: {metric.config.base}{pretty_labels(labels)}. Starting counter at {v}"
            )
            incr = v

        metric.counter.labels(**labels).inc(incr)

        metric.previous_values_by_key[key] = v


class Process:
    def __init__(self, metrics: List[Metrics]):
        self.metrics = metrics

    async def load(self, timestamp):
        task_list = [load_metric(metric, timestamp) for metric in self.metrics]
        await asyncio.gather(*task_list)

    async def tick(self, timestamp):
        task_list = [tick_metric(metric, timestamp) for metric in self.metrics]
        await asyncio.gather(*task_list)
