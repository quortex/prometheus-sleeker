import asyncio
import logging
from typing import List

from . import prom
from .metric import Metrics
from .options import Options

logger = logging.getLogger(__name__)


def pretty_labels(labels):
    """
    Display the labels in a form usable in promql queries
    """
    return "{" + ",".join([f'{key}="{value}"' for key, value in labels.items()]) + "}"


async def load_metric(metric: Metrics, timestamp, options: Options):
    """
    Fetch Prometheus metrics (input and output) to compute the starting values of the output
    metrics. The prometheus_client Counter is not incremented here because this function is
    called in parallel for every metrics, and some calls may fail, in which case the whole
    loading operation can be performed again.
    """
    result = []

    # Max 11000 points (Prometheus limit), with 5s resolution, we can fetch 15 hours of data
    # EDIT 1: Increase the resolution to 15 seconds as it is the scrape_interval configured in
    # prometheus
    # EDIT 2: For performance reasons, we only fetch 6 hours of data
    fine_duration_s = 21600
    start = timestamp - fine_duration_s  # now minus the window duration

    # Get the last available value of the output metric. We are interested in the value, to start our counter at this value,
    # and the timestamp, because we will have to catch up the input counter increments from this time, until now.

    query = (
        "query_range?query="
        + metric.get_recatch_query()
        + f"&start={start}&end={timestamp}&step=15s"
    )
    data = await prom.fetch(query)

    # Store the values and timestamp of the output metrics
    recatch_dots_by_key = {}

    for element in data:
        labels = metric.filter_labels(element["metric"])
        key = tuple(labels.values())

        last_dot = element["values"][-1]

        # Convert counter value from str to int
        last_dot = last_dot[0], float(last_dot[1])

        logger.debug(f"Found dot {last_dot} for {metric.output}{pretty_labels(labels)}")
        recatch_dots_by_key[key] = last_dot

    # Fine tuned query to compute input increments

    query = (
        "query_range?query="
        + metric.get_query()
        + f"&start={start}&end={timestamp}&step=15s"
    )
    data = await prom.fetch(query)

    for element in data:
        labels = element["metric"]
        key = tuple(labels.values())

        values = element["values"]

        if key in recatch_dots_by_key:

            # Store the last seen input counter
            metric.previous_values_by_key[key] = float(values[-1][1])

            # Remove the current metric from recatch_dots_by_key.
            last_timestamp, counter_value = recatch_dots_by_key.pop(key)

            # Keep only the values seen during the sleeker unavailability
            catchup_values = [[t, v] for [t, v] in values if t >= last_timestamp]

            input_counter_incr = 0
            for i in range(len(catchup_values) - 1):
                tn, vn = catchup_values[i]
                tnp, vnp = catchup_values[i + 1]
                vn, vnp, tn, tnp = float(vn), float(vnp), float(tn), float(tnp)
                increment = vnp - vn if vnp >= vn else vnp
                input_counter_incr += increment

            logger.debug(
                f"Catchup: {counter_value} + {input_counter_incr} for {metric.output}{pretty_labels(labels)}"
            )
            result.append(
                (metric.counter.labels(**labels), counter_value + input_counter_incr)
            )

    if recatch_dots_by_key:
        # Some output values do not have the matching input value within the
        # fine tuned interval. Check if the input value has existed during a
        # longer (ttl) period.

        existing_keys = set()
        query = "query?query=" + metric.get_liveness_query(options.ttl)
        data = await prom.fetch(query)
        for element in data:
            labels = element["metric"]
            key = tuple(labels.values())
            existing_keys.add(key)

        for key, dot in recatch_dots_by_key.items():
            _timestamp, counter_value = dot
            labels = metric.key_to_label(key)
            if key in existing_keys:
                # The input metrics has lived during the ttl, keep the output metrics where we have seen it
                logger.warning(
                    f"No value found for {metric.input}{pretty_labels(labels)} during previous {fine_duration_s}s, but found in last {options.ttl}."
                )
                result.append((metric.counter.labels(**labels), counter_value))
            else:
                # Forget the output metrics
                logger.warning(
                    f"No value found for {metric.input}{pretty_labels(labels)} during previous {options.ttl}, metric removed."
                )

    return result


async def tick_metric(metric, timestamp):
    query = "query?query=" + metric.get_query() + f"&time={timestamp}"
    data = await prom.fetch(query)
    for element in data:
        labels = metric.filter_labels(element["metric"])
        key = tuple(labels.values())

        value = element["value"]

        if not value:
            logger.warning(f"No value for {metric.input}{pretty_labels(labels)}")
            continue

        _t, v = value
        v = float(v)

        previous_value = metric.previous_values_by_key.get(key)
        if previous_value is not None:
            incr = v - previous_value
            if incr < 0:
                # Counter has reset
                logger.info(
                    f"Reset found on counter {metric.input}{pretty_labels(labels)}"
                )
                incr = v
        else:
            logger.info(
                f"New labels found: {metric.input}{pretty_labels(labels)}. Starting counter at {v}"
            )
            incr = v

        metric.counter.labels(**labels).inc(incr)

        metric.previous_values_by_key[key] = v


class Process:
    def __init__(self, config):
        self.metrics: List[Metrics] = config["metrics"]
        self.options: Options = config["options"]

    async def load(self, timestamp):
        task_list = [
            load_metric(metric, timestamp, self.options) for metric in self.metrics
        ]
        task_results = await asyncio.gather(*task_list)

        # Here, all Prometheus operations are done successfully. We can now set the counters
        # initial values

        for task_result in task_results:
            for counter, initial_value in task_result:
                counter.inc(initial_value)

    async def tick(self, timestamp):
        task_list = [tick_metric(metric, timestamp) for metric in self.metrics]
        await asyncio.gather(*task_list)
