import venusian
from zope.interface.interfaces import IInterface

from .interfaces import CATEGORY

__all__ = ('adapter',)


class adapter(object):

    def __init__(self, required, provided=None, name=u''):
        if IInterface.providedBy(required):
            required = (required,)

        self.name = name
        self.required = required
        self.provided = provided

    def register(self, scanner, name, wrapped):
        scanner.config.add_adapter(
            wrapped, required=self.required,
            provided=self.provided, name=self.name)

    def __call__(self, factory):
        venusian.attach(factory, self.register, category=CATEGORY)
        return factory
