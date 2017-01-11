""" swagger format declartion """
import venusian
from .interfaces import CATEGORY

__all__ = ('format', 'SwaggerFormat')


class SwaggerFormat(object):

    def __init__(self, name):
        self.format = name

    def to_wire(self, item):
        raise NotImplementedError

    def to_python(self, value):
        raise NotImplementedError

    def validate(self, value):
        pass


class format(object):

    def __init__(self, name):
        self.name = name

    def __call__(self, wrapped):
        assert issubclass(wrapped, SwaggerFormat)

        def register(scanner, name, wrapped):
            scanner.config.loader.register_format(wrapped(self.name))

        venusian.attach(wrapped, register, category=CATEGORY)
        return wrapped
