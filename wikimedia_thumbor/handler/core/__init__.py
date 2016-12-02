from tc_core import Extension, Extensions
from .core import CoreHandler


__all__ = ['CoreHandler']

extension = Extension('wikimedia_thumbor.handler.core')
extension.add_handler(CoreHandler.regex(), CoreHandler)

Extensions.register(extension)
