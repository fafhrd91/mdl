""" Response stream """
from ..declarations import implements
from ..web.interfaces import IStream, IStreamWriter

__all__ = ('Stream',)


class Stream(object):
    implements(IStream)

    def __init__(self, coro):
        self.coro = coro

    def __call__(self, stream):
        return (yield from self.coro(stream))


class StreamWriter(object):
    implements(IStreamWriter)

    def __init__(self, params, request, response):
        self._params = params
        self._request = request
        self._resp = response
        self._eof_sent = False

    @property
    def params(self):
        return self._params

    @property
    def request(self):
        return self._request

    def write(self, data):
        assert isinstance(data, (bytes, bytearray, memoryview)), \
            "data argument must be byte-ish (%r)" % type(data)

        if self._eof_sent:
            raise RuntimeError("Cannot call write() after write_eof()")
        if self._resp is None:
            raise RuntimeError("Cannot call write() before start()")

        if data:
            return self._resp.write(data)
        else:
            return ()

    def drain(self):
        if self._resp is None:
            raise RuntimeError("Response has not been started")
        yield from self._resp.transport.drain()

    def write_eof(self):
        if self._eof_sent:
            return
        if self._resp is None:
            raise RuntimeError("Response has not been started")

        yield from self._resp.write_eof()
        self.eof_sent = True
