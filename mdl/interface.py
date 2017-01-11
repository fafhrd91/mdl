""" mdl specific interface """
from __future__ import absolute_import
from zope.interface.interface import Attribute as _Attribute
from zope.interface.interface import InterfaceClass as _InterfaceClass

__all__ = ('Interface', 'Attribute')


class InterfaceClass(_InterfaceClass):
    """ Custom mdl interface implementation with contracts support """

    def __init__(self, name, bases=(), attrs=None, __doc__=None,
                 __module__=None):
        super(InterfaceClass, self).__init__(
            name, bases=bases, attrs=attrs,
            __doc__=__doc__, __module__=__module__)

        self.__contract__ = parse_iface_contract(self)

    def contract(self, ob, logger=None):
        """Bind object to contract"""
        return self.__contract__.bind(ob, logger=logger)

    def query(self, obj, *args, **kwargs):
        """Adapt an object to the interface"""
        return super(InterfaceClass, self).__call__(obj, *args, **kwargs)

    def __call__(self, obj, *args, **kwargs):
        """Adapt an object to the interface"""
        if args:
            return super(InterfaceClass, self).__call__(
                (obj,) + args, **kwargs)
        else:
            return super(InterfaceClass, self).__call__(
                obj, **kwargs)


class Attribute(_Attribute):
    """Interface attribute"""

    def __init__(self, __name__, __doc__='', spec=''):
        super(Attribute, self).__init__(__name__, __doc__)

        self.spec = spec


from .contracts.parser import parse_iface_contract  # noqa

Interface = InterfaceClass("Interface", __module__='mdl.interface')
