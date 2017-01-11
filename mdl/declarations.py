import sys
from zope.interface import implementer, directlyProvides

__all__ = ('implements', 'implementer', 'directlyProvides')


class ImplementsPlaceholder(object):

    def __init__(self):
        self.interfaces = set()

    def __iter__(self):
        return iter(self.interfaces)

    def implements(self, *interfaces):
        self.interfaces.update(interfaces)


def implements(*interfaces):
    """Declare interfaces implemented by instances of a class

      This function is called in a class definition.

      The arguments are one or more interfaces or interface
      specifications (IDeclaration objects).

      The interfaces given (including the interfaces in the
      specifications) are added to any interfaces previously
      declared.

      Previous declarations include declarations for base classes
      unless implementsOnly was used.

      This function is provided for convenience. It provides a more
      convenient way to call classImplements. For example::

        class C:
            implements(I1)

      is equivalent to calling::

        class C:
            pass
        classImplements(C, I1)

      after the class has been created.
    """
    frame = sys._getframe(1)
    locals = frame.f_locals

    implemented = locals.get('__implemented__')
    if implemented is None:
        locals['__implemented__'] = implemented = ImplementsPlaceholder()

    implemented.implements(*interfaces)
