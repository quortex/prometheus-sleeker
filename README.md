[![Quortex][logo]](https://quortex.io)


# Prometheus counter sleeker

## Why

When a Prometheus counter is reset, it can be harder to perform some operations. This is
particularly true when we need to get the exact increase of a counter during a specific interval.

Existing Prometheus functions which handle counter restarts are based on extrapolation, so the
given result is not exact.

For example, we may use this formula:

my_metric - (my_metric offset 30m)

By perfomring this operation on a time range with a step of 30 minutes (the same step as the time
offset), this leads to the exact counter increment every 30 minutes.

But the counter must not restart !

The aim of this software is to create new metrics based on existing counter metrics, but without
the eventual resets.

How this works:
- At startup, we fetch the latest value of our generated output metric to start at this value
- At regular interval, we fetch the base metric, and reflect the increments on our metric

## Command line options

- configuration file:

The default configuration file is ./config.json
This can be changed by running the sleeker with --config my_conf_file on the command line.

- verbosity

The verbosity can be increased with --verbose and decreased with --quiet

## Environment variables configuration

The Prometheus instance URL can be configured with:

- PROMETHEUS_URL
- PROMETHEUS_PORT

The default is localhost:9090

## Configuration file

Example:
```
{
    "options": {
        "ttl": "10d"
    },
    "metrics": [
        {
            "input": "my_input_metric",
            "output": "my_output_metric",
            "filters": "my_label_a='0'",
            "aggregation_labels": ["my_label_b", "my_label_c"]
        }
    ]
}

```

The configuration file must be a json object containing the following parameters:


- options [optionnal object]:

    - ttl [optionnal string]

        During startup, if a input metric has not be seen during this duration, it will be discared.

- metrics [List of object]:

    - input [string]

        Name of the input metric. If this metric is a counter, the ending _total must be written.

    - output [string]

        Name of the metric which will be generated by the sleeker. The ending _total is not mandatory, but will be added anyway since the metric is a counter.

    - description [optionnal string]

        Description of the output metric. Can be anything. If omitted, a default will be provided.

    - filtering [optionnal string]

        Filters to apply on the input metric, before any aggregation. The syntax is the one used in promql, without any curly braces.

        eg: "job='prometheus',group=~'canary.*'"


    - aggregation_labels [list of string]

        Labels used to compute the key used to identify a unique entity. If two counters have the same values for all labels in the aggregation_labels list, they will be considered the same object, and result in one output counter.
        This can be useful to skip labels like the pod IP in a kubernetes cluster, so a single counter will be generated even if the pod generating the input metric is moved.
        All input counters sharing the same key will be aggregated in a single output counter. The aggregation performed can be configured with the aggregation_operation


    - aggregation_operation [optionnal string]

        How to aggregate input counters sharing the same key (see aggregation_labels).
        Default to "sum".
