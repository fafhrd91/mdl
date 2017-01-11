import sys

from . import interfaces
from .declarations import implements, directlyProvides

__all__ = ('Context',)


class Context(object):
    implements(interfaces.IContext)

    def __init__(self, markers=()):
        self._contexts = {}
        self._stack = [ContextItem()]

        if markers:
            directlyProvides(self, markers)

    def __del__(self):
        if len(self._stack) > 1:
            # something is wrong
            pass

        self._stack[0]._teardown()

    def __enter__(self):
        item = ContextItem()
        self._stack.append(item)
        return item

    def __exit__(self, exc_type, exc_value, exc_tb):
        item = self._stack.pop()
        item._teardown()

        if len(self._stack) == 1:
            self._stack[0]._teardown()

        return False

    def teardown(self):
        if len(self._stack) > 1:
            # something is wrong
            pass

        self._stack[0]._teardown()

    def register_teardown_callback(self, callback):
        """Register callable to be called when context exits"""
        self._stack[-1].register_teardown_callback(callback)


class ContextItem(object):

    def __init__(self):
        self._teardown_callbacks = []

    def _teardown(self, exc=None):
        callbacks = self._teardown_callbacks
        self._teardown_callbacks = []

        if exc is None:
            exc = sys.exc_info()[1]

        for func in reversed(callbacks):
            func(exc)

    def register_teardown_callback(self, callback):
        self._teardown_callbacks.append(callback)
