""" aiohttp related interfaces """
from ..interface import Interface, Attribute


class IRoute(Interface):
    """ Route """

    op = Attribute('op', 'Swagger Operation',
                   spec='bravado_core.operation.Operation')
