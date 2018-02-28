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

    try:
        thumbor_version = pkg_resources.get_distribution('thumbor').version
    except pkg_resources.DistributionNotFound:
        thumbor_version = None

    try:
        wikimedia_thumbor_version = pkg_resources.get_distribution('wikimedia_thumbor').version
    except pkg_resources.DistributionNotFound:
        wikimedia_thumbor_version = None

    extras = {
        'url': url,
        'thumbor-request-id': request_id,
        'thumbor-version': thumbor_version,
        'wikimedia-thumbor-version': wikimedia_thumbor_version
    }
    return extras
