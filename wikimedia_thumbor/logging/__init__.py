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


def log_extra(context):
    extras = {
        'url': context.request.url,
        'thumbor-request-id': context.request_handler.request.headers.get('Thumbor-Request-Id', 'None')
    }
    return extras
