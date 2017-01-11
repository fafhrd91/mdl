from . import interfaces
from .response import Response
from ..context import Context
from ..declarations import implements
from ..swagger import Location

__all__ = ('WebContext',)


class WebContext(Context):
    implements(interfaces.IWebContext)

    def __init__(self, op, request, params, keep_alive=None, markers=()):
        super(WebContext, self).__init__(markers)

        self.op = op
        self.params = params
        self.request = request
        self.response = Response()

        self._keep_alive = keep_alive
        self._tcp_cork = None
        self._tcp_nodelay = None

    @property
    def keep_alive(self):
        return self._keep_alive

    def force_close(self):
        self._keep_alive = False

    @property
    def tcp_nodelay(self):
        return self._tcp_nodelay

    def set_tcp_nodelay(self, value):
        self._tcp_nodelay = value

    @property
    def tcp_cork(self):
        return self._tcp_cork

    def set_tcp_cork(self, value):
        self._tcp_cork = value


class Params(object):

    def __init__(self, **params):
        mapping = self.__mapping__
        self.__dict__.update(
            ((mapping[name], value)
             for name, value in params.items())
        )

    @staticmethod
    def generate_class(op):
        """ Generate class for swagger operation """
        slots = {'__oper__'}

        mapping = {}
        attrs = {'__oper__': op, '__mapping__': mapping}

        for name, element in op.params.items():
            if element.location == Location.header:
                attr_name = 'HTTP_%s' % name.replace('-', '_')
            else:
                attr_name = name

            slots.add(attr_name)
            attrs[attr_name] = ParamsProperty(attr_name)
            element.attr_name = attr_name
            mapping[name] = attr_name

        name = 'Params_%s' % op.operation_id
        cls = type(name, (Params,), attrs)
        cls.__slots__ = tuple(slots)

        return cls


class ParamsProperty(object):

    def __init__(self, name):
        self.name = name

    def __get__(self, ob, type):
        try:
            return ob.__dict__[self.name]
        except KeyError:
            raise AttributeError

    def __set__(self, ob, val):
        raise AttributeError
