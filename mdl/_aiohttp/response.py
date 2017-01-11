""" Response renderer """
from aiohttp.protocol import HttpVersion10, HttpVersion11
from aiohttp.protocol import WebResponse as ResponseImpl

from ..web import hdrs
from ..web.interfaces import IStream
from ..web.response import ContentCoding

from .stream import StreamWriter


class ResponseRenderer(object):

    def __init__(self, ctx, body):
        self.ctx = ctx
        self.op = ctx.op
        self.request = None
        self.response = ctx.response
        self.body = body

        self.writer = None
        self.eof_sent = False
        self.resp_impl = None
        self.keep_alive = None

    @property
    def status(self):
        return self.response.status

    @property
    def body_length(self):
        return self.resp_impl.body_length

    @property
    def output_length(self):
        return self.resp_impl.output_length

    def prepare(self, request,
                HttpVersion10=HttpVersion10,
                HttpVersion11=HttpVersion11,
                CONNECTION=hdrs.CONNECTION,
                DATE=hdrs.DATE,
                SERVER=hdrs.SERVER,
                SET_COOKIE=hdrs.SET_COOKIE,
                TRANSFER_ENCODING=hdrs.TRANSFER_ENCODING):

        yield from request._prepare_hook(self.response)

        # set content type
        if self.response.content_type is None:
            self.response.content_type = self.op.produces[0]

        # respone body
        if isinstance(self.body, str):
            charset = self.response.charset
            if charset is None:
                charset = 'utf-8'
                self.response.charset = charset

            body = self.body.encode(charset)
        else:
            body = self.body

        # keep-alive
        keep_alive = self.ctx.keep_alive
        if keep_alive is None:
            keep_alive = request.keep_alive
        self.keep_alive = keep_alive

        version = request.version

        resp_impl = self.resp_impl = ResponseImpl(
            request._writer,
            self.response.status,
            version,
            not keep_alive,
            self.response.reason)

        headers = self.response.headers
        # for cookie in self.ctx.response.cookies.values():
        #    value = cookie.output(header='')[1:]
        #    headers.add(SET_COOKIE, value)

        if self.response.content_coding is not None:
            self._start_compression(request)

        if self.response.chunked:
            if request.version != HttpVersion11:
                raise RuntimeError(
                    "Using chunked encoding is forbidden "
                    "for HTTP/{0.major}.{0.minor}".format(request.version))
            resp_impl.chunked = True
            if self.response.chunk_size:
                resp_impl.add_chunking_filter(self.response.chunk_size)
            headers[TRANSFER_ENCODING] = 'chunked'
        else:
            content_length = self.response.content_length
            if content_length is None:
                self.response.content_length = len(body)

            resp_impl.length = self.response.content_length

        headers.setdefault(DATE, request.time_service.strtime())
        headers.setdefault(SERVER, resp_impl.SERVER_SOFTWARE)
        if CONNECTION not in headers:
            if keep_alive:
                if version == HttpVersion10:
                    headers[CONNECTION] = 'keep-alive'
            else:
                if version == HttpVersion11:
                    headers[CONNECTION] = 'close'

        resp_impl.headers = headers
        resp_impl.send_headers()

        self.writer = StreamWriter(self.ctx.params, request, resp_impl)

        if IStream.providedBy(body):
            yield from body(self.writer)
        else:
            yield from self.writer.write(body)

    def _do_start_compression(self, coding):
        if coding != ContentCoding.identity:
            self.response.headers[hdrs.CONTENT_ENCODING] = coding.value
            self.response.content_length = None
            self.resp_impl.add_compression_filter(coding.value)

    def _start_compression(self, request):
        if self.response.content_coding is not None:
            self._do_start_compression(self.response.content_coding)
        else:
            accept_encoding = request.headers.get(
                hdrs.ACCEPT_ENCODING, '').lower()
            for coding in ContentCoding:
                if coding.value in accept_encoding:
                    self._do_start_compression(coding)
                    return

    def write_eof(self):
        yield from self.writer.write_eof()
