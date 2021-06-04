import re


DEFAULT_TTL = "1d"


def validate_ttl(ttl: str):
    units = ["y", "w", "d", "h", "m", "s", "ms"]
    for unit in units:
        pattern = r"^\d+" + unit + "$"
        match = re.match(pattern, ttl)
        if match:
            return
    raise ValueError(
        f"Invalide ttl format {ttl}. It must match a Prometheus time duration (https://prometheus.io/docs/prometheus/latest/querying/basics/#time-durations)"
    )


class Options:
    def __init__(self, **kwargs) -> None:
        self.ttl = kwargs.get("ttl", DEFAULT_TTL)
        validate_ttl(self.ttl)
