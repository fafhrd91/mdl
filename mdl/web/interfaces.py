from .. import interface
from ..interfaces import IContext


class IRequest(interface.Interface):
    """ web request """


class IResponse(interface.Interface):
    """ response """


class IParameters(interface.Interface):
    """ parameters """


class IWebContext(IContext):
    """Web handler context"""

    params = interface.Attribute('Parameters', spec='IParameters')

    request = interface.Attribute('Request', spec='IRequest')
    response = interface.Attribute('Response', spec='IResponse')


class IStream(interface.Interface):
    """ stream handler """

    def __call__(stream):
        """ call stream from response renderer

        :type stream: IStreamWriter
        """


class IStreamWriter(interface.Interface):
    """ Writer object for stream """

    params = interface.Attribute('Parameters', spec='IParameters')
    request = interface.Attribute('Request', spec='IRequest')

    def write(data):
        """ write data to stream

        :type data: bytes | bytearray | memoryview
        """

    def write_eof():
        """ write eof to stream,
        writer object is not usable after calling this function

        :rtype: None
        """
