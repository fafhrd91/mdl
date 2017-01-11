""" Swagger specific constants """
import enum
import six


class Location(enum.Enum):

    path = 'path'
    query = 'query'
    header = 'header'
    form_data = 'formData'
    body = 'body'

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.value == other.value
        if isinstance(other, six.string_types):
            return self.value == other

        return NotImplemented
