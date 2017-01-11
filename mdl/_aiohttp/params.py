"""Unmarshall swagger request parameters."""
from functools import partial
from six import iteritems

from bravado_core import schema
from bravado_core.exception import SwaggerMappingError
from bravado_core.param import cast_request_param, get_param_type_spec
from bravado_core.param import unmarshal_collection_format
from bravado_core.unmarshal import unmarshal_schema_object
from bravado_core.validate import validate_schema_object
from bravado_core.validate import validate_security_object

from ..swagger import Location


async def unmarshal_request(cls, request):
    """Unmarshal Swagger request parameters from the passed in request like
    object.

    :type request: :class: `aiohttp.web.Request`.
    :type op: :class:`bravado_core.operation.Operation`
    :returns: dict where (key, value) = (param_name, param_value)
    """
    request_data = {}
    for param_name, param in iteritems(cls.__oper__.params):
        param_value = await unmarshal_param(param, request)
        request_data[param.attr_name] = param_value

    if cls.__oper__.swagger_spec.config['validate_requests']:
        validate_security_object(cls.__oper__, request_data)

    return cls(**request_data)


async def unmarshal_param(param, request):
    """Unmarshal the given parameter from the passed in request like object.

    :type param: :class:`bravado_core.param.Param`
    :type request: :class:`bravado_core.request.IncomingRequest`
    :return: value of parameter
    """
    swagger_spec = param.swagger_spec
    deref = swagger_spec.deref
    param_spec = deref(get_param_type_spec(param))
    location = param.location
    param_type = deref(param_spec.get('type'))
    cast_param = partial(cast_request_param, param_type, param.name)

    default_value = schema.get_default(swagger_spec, param_spec)

    if location == Location.path:
        raw_value = cast_param(request.match_info.get(param.name, None))
    elif location == Location.query:
        raw_value = cast_param(request.query.get(param.name, default_value))
    elif location == Location.header:
        raw_value = cast_param(request.headers.get(param.name, default_value))
    elif location == Location.form_data:
        if param_type == 'file':
            raw_value = request.files.get(param.name, None)
        else:
            raw_value = cast_param(request.form.get(param.name, default_value))
    elif location == Location.body:
        # TODO: verify content-type header
        try:
            raw_value = request.json()
        except ValueError as json_error:
            raise SwaggerMappingError("Error reading request body JSON: {0}".
                                      format(str(json_error)))
    else:
        raise SwaggerMappingError(
            "Don't know how to unmarshal_param with location {0}".
            format(location))

    if raw_value is None and not schema.is_required(swagger_spec, param_spec):
        return None

    if param_type == 'array' and location != Location.body:
        raw_value = unmarshal_collection_format(
            swagger_spec, param_spec, raw_value)

    if swagger_spec.config['validate_requests']:
        validate_schema_object(swagger_spec, param_spec, raw_value)

    value = unmarshal_schema_object(swagger_spec, param_spec, raw_value)
    return value
