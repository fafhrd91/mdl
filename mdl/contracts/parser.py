""" PyContracts support """
from __future__ import absolute_import

import six
from contracts.main import parse_flexible_spec
from contracts.interface import ContractException, MissingContract
from contracts.interface import ContractNotRespected
from zope.interface.interface import Method

from ..interface import Attribute
from .contract import InterfaceContract
from .contract import AdapterContract, AttributeContract, MethodContract
from .docstring_parsing import DocStringInfo

__all__ = ('parse_iface_contract',)


def parse_iface_contract(iface):
    contracts = []
    for name, element in iface.namesAndDescriptions(1):
        __interface__ = iface  # noqa, we need this for Reference contract

        if isinstance(element, Method):
            if element.kwargs:
                raise ContractException(
                    '"**%s" is not supported for %s.%s' % (
                        element.kwargs,
                        iface.__identifier__, element.__name__))

            if element.varargs:
                raise ContractException(
                    '"*%s" is not supported for %s.%s' % (
                        element.varargs,
                        iface.__identifier__, element.__name__))

            accepts_dict, returns, exceptions = \
                parse_contracts_from_method(iface, element)
            if not accepts_dict and not returns:
                raise ContractException(
                    'No contract specified in docstring for %s.%s' % (
                        iface.__identifier__, element.__name__))

            if returns is None:
                result_contract = None
            else:
                result_contract = parse_flexible_spec(returns)

            args_contract = dict(
                (x, parse_flexible_spec(accepts_dict[x]))
                for x in accepts_dict)

            exceptions = map(parse_flexible_spec, exceptions)

            for arg, value in element.optional.items():
                contract = args_contract[arg]
                try:
                    contract._check_contract({}, value, silent=True)
                except ContractNotRespected:
                    raise ContractException(
                        'Default value for argument "%s=%r" '
                        'to %s.%s does not satisfy contract %r' % (
                            arg, value,
                            iface.__identifier__, element.__name__,
                            accepts_dict[arg]))

            contracts.append(
                MethodContract(iface, element,
                               args_contract, result_contract, exceptions))

        elif isinstance(element, Attribute):
            spec = element.spec
            if not isinstance(spec, six.string_types):
                raise ContractException(
                    'String type is required for attribute contract '
                    'definition: %s.%s got: %s' % (
                        iface.__identifier__, element.__name__, spec))

            if not spec.strip():
                raise ContractException(
                    'No contract specified for %s.%s attribute' % (
                        iface.__identifier__, element.__name__))

            contract = parse_flexible_spec(spec)
            contracts.append(
                AttributeContract(iface, element, contract))

    # get interface adapter contract
    adapter = None
    args, exceptions = parse_adapter_contract(iface)
    if args:
        adapter = AdapterContract(
            iface,
            map(parse_flexible_spec, args),
            map(parse_flexible_spec, exceptions))

    return InterfaceContract(iface, contracts, adapter)


def get_all_arg_names(spec):
    possible = spec.positional + (
        spec.varargs, spec.kwargs) + tuple(spec.optional.keys())
    all_args = [x for x in possible if x]
    return set(all_args)


def remove_quotes(x):
    """ Removes the double back-tick quotes if present. """
    if x is None:
        return None
    if x.startswith('``') and x.endswith('``') and len(x) > 3:
        return x[2:-2]
    elif x.startswith('``') or x.endswith('``'):
        msg = 'Malformed quoting in string %r.' % x
        raise ContractException(msg)
    else:
        return x


def parse_contracts_from_method(iface, method):
    annotations = DocStringInfo.parse(method.__doc__)

    if annotations.args:
        raise ContractException(
            'Positional arguments are not supported for method contracts.')

    if len(annotations.returns) > 1:
        raise ContractException('More than one return type specified.')

    if len(annotations.returns) == 0:
        returns = None
    else:
        returns = remove_quotes(annotations.returns[0].type)

    exceptions = tuple(remove_quotes(exc.type)
                       for exc in annotations.exceptions)

    # These are the annotations
    params = annotations.params
    name2type = dict(
        (name, remove_quotes(params[name].type)) for name in params)

    # Check the ones that do not have contracts specified
    nullparams = [name for name in params if params[name].type is None]
    if nullparams:
        msg = (
            'The parameter(s) %r in "%s.%s" docstring have no type statement.'
            % (",".join(nullparams), iface.__identifier__, method.__name__))
        msg += """

Note: you can use the asterisk if you do not care about assigning
a contract to a certain parameter:

    :param x:
    :type x: *
"""
        raise MissingContract(msg)

    # Let's look at the parameters:
    all_args = get_all_arg_names(method)

    # Check we don't have extra:
    for name in name2type:
        if name not in all_args:
            msg = ('A contract was specified for argument %r which I cannot'
                   ' find in my list of arguments for "%s.%s(%r)"' %
                   (name, iface.__identifier__, method.__name__, all_args))
            raise ContractException(msg)

    if len(name2type) != len(all_args):  # pragma: no cover
        raise ContractException()

    return name2type, returns, exceptions


def parse_adapter_contract(iface):
    annotations = DocStringInfo.parse(iface.__doc__, True)

    if annotations.params:
        raise ContractException(
            'Only positional arguments '
            'are not supported for interface adater contract.')

    args = tuple(remove_quotes(arg.type) for arg in annotations.args)
    exceptions = tuple(remove_quotes(exc.type)
                       for exc in annotations.exceptions)

    return args, exceptions
