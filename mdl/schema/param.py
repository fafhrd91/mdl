""" Parameter definition """
import enum
from bravado_core.param import Param as _Param


class ParamLocation(enum.Enum):

    path = 'path'
    query = 'query'
    header = 'header'
    formData = 'formData'
    body = 'body'


class ParamDataType(enum.Enum):

    path = 'path'
    query = 'query'
    header = 'header'
    formData = 'formData'
    body = 'body'


class Param(_Param):

    def __init__(self, field, location):
        pass
