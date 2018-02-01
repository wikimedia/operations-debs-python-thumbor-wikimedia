def record_timing(context, duration, statsd_key, header_name=None):
    duration = int(round(duration.total_seconds() * 1000))

    context.metrics.timing(
        statsd_key,
        duration
    )

    if header_name is not None:
        context.request_handler.add_header(
            header_name,
            duration
        )
