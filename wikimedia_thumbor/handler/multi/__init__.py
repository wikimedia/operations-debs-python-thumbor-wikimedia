from tc_core import Extension, Extensions
from .multi import MultiHandler


__all__ = ['MultiHandler']

extension = Extension('wikimedia_thumbor.handler.multi')
extension.add_handler(MultiHandler.regex(), MultiHandler)

Extensions.register(extension)
