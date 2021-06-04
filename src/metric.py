from prometheus_client import Counter


class Metrics:
    def __init__(self, **kwargs) -> None:

        # Configuration
        self.base = kwargs["base"]
        self.name = kwargs["name"]
        self.description = kwargs["description"]
        self.aggregation_labels = kwargs["aggregation_labels"]
        self.aggregation_operation = kwargs["aggregation_operation"]

        # Prometheus client
        self.counter = Counter(self.name, self.description, self.aggregation_labels)

        # Store the last values seen in the base counter, to compute the
        # increment when we read the counter again.
        self.previous_values_by_key = {}

    def get_query(self):
        by_clause = ", ".join(self.aggregation_labels)
        return f"{self.aggregation_operation} by ({by_clause})({self.base})"

    def get_liveness_query(self, ttl: str):
        """
            To check the existance of a key
        """
        by_clause = ", ".join(self.aggregation_labels)
        return f"{self.aggregation_operation} by ({by_clause})(max_over_time({self.base}[{ttl}]))"

    def get_recatch_query(self):
        return f"{self.name}_total"

    def filter_labels(self, labels):
        return {label: labels[label] for label in self.aggregation_labels}

    def key_to_label(self, key: tuple):
        return {
            label: key[index] for index, label in enumerate(self.aggregation_labels)
        }
