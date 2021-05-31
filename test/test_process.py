import pytest
from prometheus_client import REGISTRY

from src.metric import MetricConfig, Metrics
from src.process import Process


def test_demo_mode_disabled():
    assert True


def mocked_prom_reply(data):
    return {
        "status_code": 200,
        "status": "success",
        "data": {"result": data},
    }


@pytest.mark.asyncio
async def test_load_when_base_counter_is_still_present(httpx_mock):

    # Mock first call to Prometheus: the output metric
    data_1 = [
        {
            "metric": {
                "__name__": "output_metric_1",
                "a": "1",
                "b": "foo",
                "dummy_label": "my_dummy_label_value",
            },
            "values": [[100000, "20"], [100005, "21"],],
        }
    ]
    httpx_mock.add_response(json=mocked_prom_reply(data_1))

    # Mock second call to Prometheus: the base metric
    data_2 = [
        {
            "metric": {
                "__name__": "base_metric_1",
                "a": "1",
                "b": "foo",
                "dummy_label": "my_dummy_label_value",
            },
            "values": [[100000, "3"], [100005, "4"], [100010, "1"], [100015, "2"],],
        }
    ]
    httpx_mock.add_response(json=mocked_prom_reply(data_2))

    metric_config = MetricConfig(
        "base_metric_1", "output_metric_1", "Lorem ipsum", ["a", "b"], "sum"
    )
    process = Process([Metrics(metric_config)])

    t = 100015
    await process.load(t)

    metric_value = REGISTRY.get_sample_value(
        "output_metric_1_total", labels={"a": "1", "b": "foo"}
    )
    assert metric_value == 23


@pytest.mark.asyncio
async def test_load_when_base_counter_is_no_longer_present(httpx_mock):

    data_1 = [
        {
            "metric": {
                "__name__": "output_metric_2",
                "a": "1",
                "b": "foo",
                "dummy_label": "my_dummy_label_value",
            },
            "values": [[100000, "20"], [100005, "21"],],
        }
    ]
    httpx_mock.add_response(json=mocked_prom_reply(data_1))

    data_2 = []
    httpx_mock.add_response(json=mocked_prom_reply(data_2))

    metric_config = MetricConfig(
        "base_metric_2", "output_metric_2", "Lorem ipsum", ["a", "b"], "sum"
    )
    process = Process([Metrics(metric_config)])

    t = 100015
    await process.load(t)

    metric_value = REGISTRY.get_sample_value(
        "output_metric_2_total", labels={"a": "1", "b": "foo"}
    )
    assert metric_value == 21


@pytest.mark.asyncio
async def test_tick_when_output_metric_does_not_exist_yet(httpx_mock):

    data = [
        {
            "metric": {
                "__name__": "base_metric_3",
                "a": "1",
                "b": "foo",
                "dummy_label": "my_dummy_label_value",
            },
            "value": [100000, "20"],
        }
    ]
    httpx_mock.add_response(json=mocked_prom_reply(data))

    metric_config = MetricConfig(
        "base_metric_3", "output_metric_3", "Lorem ipsum", ["a", "b"], "sum"
    )
    process = Process([Metrics(metric_config)])

    t = 100015
    await process.tick(t)
    await process.tick(t)

    metric_value = REGISTRY.get_sample_value(
        "output_metric_3_total", labels={"a": "1", "b": "foo"}
    )
    assert metric_value == 20
