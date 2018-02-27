import pkg_resources


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
    try:
        url = context.request.url
    except AttributeError:
        url = None

    try:
        request_id = context.request_handler.request.headers.get('Thumbor-Request-Id', 'None')
    except AttributeError:
        request_id = None

    extras = {
        'url': url,
        'thumbor-request-id': request_id,
        'thumbor-version': pkg_resources.get_distribution('thumbor').version,
        'wikimedia-thumbor-version': pkg_resources.get_distribution('wikimedia_thumbor').version
    }
    return extras
