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
