from .interface import Interface

ANY = '*'
UNKNOW = object()
CATEGORY = 'mdl'
SENTINEL = object()


class IApplication(Interface):
    """Application"""


class IContext(Interface):
    """Transformation context"""
