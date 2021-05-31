from dataclasses import dataclass
from typing import List
from prometheus_client import Counter


@dataclass
class MetricConfig:
    base: str
    name: str
    description: str
    aggregation_labels: List[str]
    aggregation_operation: str

    @staticmethod
    def load(conf: dict):
        return MetricConfig(
            conf["base"],
            conf["name"],
            conf["description"],
            conf["aggregation_labels"],
            conf["aggregation_operation"],
        )

    def get_query(self):
        by_clause = ", ".join(self.aggregation_labels)
        return f"{self.aggregation_operation} by ({by_clause})({self.base})"

    def get_recatch_query(self):
        return f"{self.name}_total"

    def filter_labels(self, labels):
        return {label: labels[label] for label in self.aggregation_labels}

    def key_to_label(self, key: tuple):
        return {
            label: key[index] for index, label in enumerate(self.aggregation_labels)
        }


class Metrics:
    def __init__(self, metric_config: MetricConfig) -> None:
        self.config = metric_config
        self.counter = Counter(
            metric_config.name,
            metric_config.description,
            metric_config.aggregation_labels,
        )
        # Store the last values seen in the base counter, to compute the
        # increment when we read the counter again.
        self.previous_values_by_key = {}
