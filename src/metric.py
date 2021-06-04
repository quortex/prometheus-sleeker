from prometheus_client import Counter


class Metrics:
    def __init__(self, **kwargs) -> None:

        # Configuration
        self.input = kwargs["input"]
        self.output = kwargs["output"]
        self.description = kwargs.get("description", f"Sleeked from {kwargs['input']}")
        self.filtering = kwargs.get("filtering")
        self.aggregation_labels = kwargs["aggregation_labels"]
        self.aggregation_operation = kwargs.get("aggregation_operation", "sum")

        if not self.output.endswith("_total"):
            self.output += "_total"

        # Prometheus client
        self.counter = Counter(self.output, self.description, self.aggregation_labels)

        # Store the last values seen in the input counter, to compute the
        # increment when we read the counter again.
        self.previous_values_by_key = {}

    def get_query(self):
        by_clause = ", ".join(self.aggregation_labels)
        filtering_str = ""
        if self.filtering:
            filtering_str = "{" + self.filtering + "}"
        return f"{self.aggregation_operation} by ({by_clause})({self.input}{filtering_str})"

    def get_liveness_query(self, ttl: str):
        """
            To check the existance of a key
        """
        by_clause = ", ".join(self.aggregation_labels)
        filtering_str = ""
        if self.filtering:
            filtering_str = "{" + self.filtering + "}"
        return f"{self.aggregation_operation} by ({by_clause})(max_over_time({self.input}{filtering_str}[{ttl}]))"

    def get_recatch_query(self):
        return self.output

    def filter_labels(self, labels):
        return {label: labels[label] for label in self.aggregation_labels}

    def key_to_label(self, key: tuple):
        return {
            label: key[index] for index, label in enumerate(self.aggregation_labels)
        }
