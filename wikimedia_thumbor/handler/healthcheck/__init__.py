from tc_core import Extension, Extensions
from .healthcheck import HealthcheckHandler


__all__ = ['HealthcheckHandler']

extension = Extension('wikimedia_thumbor.handler.healthcheck')
extension.add_handler(HealthcheckHandler.regex(), HealthcheckHandler)

Extensions.register(extension)
