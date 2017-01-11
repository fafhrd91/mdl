import datetime
import enum
import http.server
import math
import time
from email.utils import parsedate
from http.cookies import SimpleCookie
from multidict import CIMultiDict

from . import hdrs, helpers

__all__ = ('Response', 'ContentCoding')

RESPONSES = http.server.BaseHTTPRequestHandler.responses


class ContentCoding(enum.Enum):
    # The content codings that we have support for.
    #
    # Additional registered codings are listed at:
    # https://www.iana.org/assignments/http-parameters/http-parameters.xhtml#content-coding
    deflate = 'deflate'
    gzip = 'gzip'
    identity = 'identity'


class Response(helpers.HeadersMixin):

    def __init__(self):
        self._chunked = False
        self._chunk_size = None
        self._content_coding = None
        self._cookies = SimpleCookie()
        self._headers = CIMultiDict()

        self.set_status(200)

    @property
    def chunked(self):
        return self._chunked

    @property
    def chunk_size(self):
        return self._chunk_size

    @property
    def content_coding(self):
        return self._content_coding

    @content_coding.setter
    def content_coding(self, value):
        """Enables response compression encoding."""
        if type(value) == bool:
            value = ContentCoding.deflate if value else ContentCoding.identity

        assert isinstance(value, ContentCoding), (
            "type should one of None, ContentEncoding")

        self._content_coding = value

    @property
    def status(self):
        return self._status

    @property
    def reason(self):
        return self._reason

    def set_status(self, status, reason=None):
        self._status = int(status)
        if reason is None:
            reason = Response.calc_reason(status)
        self._reason = reason

    @staticmethod
    def calc_reason(status, *, _RESPONSES=RESPONSES):
        record = _RESPONSES.get(status)
        if record is not None:
            reason = record[0]
        else:
            reason = str(status)
        return reason

    @property
    def headers(self):
        return self._headers

    @property
    def content_length(self):
        # Just a placeholder for adding setter
        return super().content_length

    @content_length.setter
    def content_length(self, value):
        if value is not None:
            value = int(value)
            # TODO: raise error if chunked enabled
            self.headers[hdrs.CONTENT_LENGTH] = str(value)
        else:
            self.headers.pop(hdrs.CONTENT_LENGTH, None)

    @property
    def content_type(self):
        # Just a placeholder for adding setter
        return super().content_type

    @content_type.setter
    def content_type(self, value):
        self.content_type  # read header values if needed
        self._content_type = str(value)
        self._generate_content_type_header()

    @property
    def charset(self):
        # Just a placeholder for adding setter
        return super().charset

    @charset.setter
    def charset(self, value):
        ctype = self.content_type  # read header values if needed
        if ctype == 'application/octet-stream':
            raise RuntimeError("Setting charset for application/octet-stream "
                               "doesn't make sense, setup content_type first")
        if value is None:
            self._content_dict.pop('charset', None)
        else:
            self._content_dict['charset'] = str(value).lower()
        self._generate_content_type_header()

    def _generate_content_type_header(self, CONTENT_TYPE=hdrs.CONTENT_TYPE):
        params = '; '.join("%s=%s" % i for i in self._content_dict.items())
        if params:
            ctype = self._content_type + '; ' + params
        else:
            ctype = self._content_type
        self.headers[CONTENT_TYPE] = ctype

    @property
    def last_modified(self, _LAST_MODIFIED=hdrs.LAST_MODIFIED):
        """The value of Last-Modified HTTP header, or None.

        This header is represented as a `datetime` object.
        """
        httpdate = self.headers.get(_LAST_MODIFIED)
        if httpdate is not None:
            timetuple = parsedate(httpdate)
            if timetuple is not None:
                return datetime.datetime(*timetuple[:6],
                                         tzinfo=datetime.timezone.utc)
        return None

    @last_modified.setter
    def last_modified(self, value):
        if value is None:
            self.headers.pop(hdrs.LAST_MODIFIED, None)
        elif isinstance(value, (int, float)):
            self.headers[hdrs.LAST_MODIFIED] = time.strftime(
                "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(math.ceil(value)))
        elif isinstance(value, datetime.datetime):
            self.headers[hdrs.LAST_MODIFIED] = time.strftime(
                "%a, %d %b %Y %H:%M:%S GMT", value.utctimetuple())
        elif isinstance(value, str):
            self.headers[hdrs.LAST_MODIFIED] = value

    def enable_chunked_encoding(self, chunk_size=None):
        """Enables automatic chunked transfer encoding."""
        self._chunked = True
        self._chunk_size = chunk_size
