from tc_core import Extension, Extensions
from .images import ImagesHandler


__all__ = ['ImagesHandler']

extension = Extension('wikimedia_thumbor.handler.images')
extension.add_handler(ImagesHandler.regex(), ImagesHandler)

Extensions.register(extension)
