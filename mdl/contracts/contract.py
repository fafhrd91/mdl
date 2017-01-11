"""Interface contract object"""
from __future__ import absolute_import
import six
import sys
import logging
from contracts.interface import ContractException, ContractNotRespected

from .extension import ID
from ..declarations import implementer
from ..verify import verifyObject
from ..interface import InterfaceClass

__all__ = (
    'InterfaceContract', 'MethodContract',
    'AttributeContract', 'ContractNotRespected')


class InterfaceContract(object):

    def __init__(self, iface, contracts, adapter=None):
        self.iface = iface
        self.elements = {}
        self.adapter = adapter

        for elem in contracts:
            self.elements[elem.name] = elem

        self._cls = construct_class(iface, self.elements)

    def verify(self, ob):
        """Raise exception if ob does not implement interface"""
        verifyObject(self.iface, ob)

    def bind(self, ob, verify=True, logger=None):
        if verify:
            self.verify(ob)

        if logger is None:
            logger = logging

        return self._cls(ob, logger)

    def bind_adapter(self, factory, logger=None):
        if logger is None:
            logger = logging
        if self.adapter is not None:
            return BoundAdapterContract(factory, self.adapter, logger)

        return factory


class AdapterContract(object):

    def __init__(self, iface, args, exceptions):
        self.name = iface.__name__
        self.iface = iface
        self.args = args
        self.exceptions = exceptions

    def _check_args_contract(self, adapter, ob, args, kwargs):
        bound = self.getcallargs(*args, **kwargs)

        for arg, contract in self.args_contract.items():
            context = {'self': ob}
            try:
                contract._check_contract(context, bound[arg], silent=True)
            except ContractNotRespected as e:
                msg = 'Breach for argument %r to %s:%s(...)\n' % (
                    arg, self.iface.__name__, self.name)
                e.error = msg + e.error
                raise e

    def __call__(self, factory, logger, *args, **kwargs):
        # self._check_args_contract(ob, args, kwargs)

        try:
            result = factory(*args, **kwargs)
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()

            # check exception contract
            context = {'factory': factory}
            for contract in self.exceptions:
                try:
                    contract._check_contract(context, exc_value, silent=True)
                except ContractNotRespected:
                    continue
                else:
                    break
            else:
                # log un-defined exception
                logger.error(
                    'Un-defined exception received from %s.%s(...)' % (
                        self.iface.__name__, self.name),
                    exc_info=(exc_type, exc_value, exc_tb))

            six.reraise(exc_type, exc_value, exc_tb)

        if not self.iface.providedBy(result):
            raise ContractException(
                'interface %s is not provided by adapted object %s' % (
                    self.name, result))

        return result


class BoundAdapterContract(object):

    def __init__(self, factory, contract, logger):
        self.factory = factory
        self.contract = contract
        self.logger = logger

    def __call__(self, *args, **kwargs):
        return self.contract(self.factory, self.logger, *args, **kwargs)


class AttributeContract(object):

    def __init__(self, iface, attr, contract):
        self.name = attr.__name__
        self.iface = iface
        self.attr = attr
        self.contract = contract

    def check_value(self, ob, value):
        context = {'self': ob}

        try:
            self.contract._check_contract(context, value, silent=True)
        except ContractNotRespected as e:
            msg = 'Breach for attribute value of %s.%s\n' % (
                self.iface.__name__, self.name)
            e.error = msg + e.error
            raise e

        type_ob = context.get(ID)
        if (type_ob is not None and
            not isinstance(value, BoundInterfaceContract) and
                isinstance(type_ob, InterfaceClass)):
            return type_ob.contract(value)

        return value


class MethodContract(object):

    def __init__(self, iface, method,
                 args_contract, result_contract, exceptions):
        self.name = method.__name__
        self.iface = iface
        self.method = method
        self.args_contract = args_contract
        self.result_contract = result_contract
        self.exceptions = exceptions

    def _check_args_contract(self, ob, args, kwargs):
        bound = self.getcallargs(*args, **kwargs)

        for arg, contract in self.args_contract.items():
            context = {'self': ob}
            try:
                contract._check_contract(context, bound[arg], silent=True)
            except ContractNotRespected as e:
                msg = 'Breach for argument %r to %s:%s(...)\n' % (
                    arg, self.iface.__name__, self.name)
                e.error = msg + e.error
                raise e

    def _check_result_contract(self, ob, result):
        context = {'self': ob}

        try:
            self.result_contract._check_contract(context, result, silent=False)
        except ContractNotRespected as e:
            msg = 'Breach for return value of %s.%s(...)\n' % (
                self.iface.__name__, self.name)
            e.error = msg + e.error
            raise e

        type_ob = context.get(ID)
        if (type_ob is not None and
            not isinstance(result, BoundInterfaceContract) and
                isinstance(type_ob, InterfaceClass)):
            return type_ob.contract(result)

        return result

    def __call__(self, ob, logger, *args, **kwargs):
        self._check_args_contract(ob, args, kwargs)

        try:
            result = getattr(ob, self.name)(*args, **kwargs)
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()

            # check exception contract
            context = {'self': ob}
            for contract in self.exceptions:
                try:
                    contract._check_contract(context, exc_value, silent=True)
                except ContractNotRespected:
                    continue
                else:
                    break
            else:
                # log un-defined exception
                logger.exception(
                    'Un-defined exception received from %s.%s(...)' % (
                        self.iface.__name__, self.name),
                    exc_info=(exc_type, exc_value, exc_tb))

            six.reraise(exc_type, exc_value, exc_tb)

        if self.result_contract is not None:
            result = self._check_result_contract(ob, result)

        return result

    def getcallargs(self, *positional, **named):
        """Get the mapping of arguments to values."""
        arg2value = {}
        args = self.method.positional

        num_pos = len(positional)
        num_total = num_pos + len(named)
        num_args = len(args)

        for arg, value in zip(args, positional):
            arg2value[arg] = value

        defaults = self.method.optional

        if 0 < num_args < num_pos:
            raise TypeError('%s() takes %s %d %s (%d given)' % (
                self.name, 'at most' if defaults else 'exactly', num_args,
                'arguments' if num_args > 1 else 'argument', num_total))
        elif num_args == 0 and num_total:
            raise TypeError(
                '%s() takes no arguments (%d given)' % (self.name, num_total))

        for arg in args:
            if isinstance(arg, str) and arg in named:
                if arg in arg2value:
                    raise TypeError(
                        "%s() got multiple values for keyword "
                        "argument '%s'" % (self.name, arg))
                else:
                    arg2value[arg] = named.pop(arg)

        if defaults:  # fill in any missing values with the defaults
            for arg, value in defaults.items():
                if arg not in arg2value:
                    arg2value[arg] = value

        if named:
            unexpected = next(iter(named))
            raise TypeError(
                "%s() got an unexpected keyword argument '%s'" %
                (self.name, unexpected))

        unassigned = num_args - len([arg for arg in args if arg in arg2value])
        if unassigned:
            num_required = num_args - len(defaults)
            raise TypeError('%s() takes %s %d %s (%d given)' % (
                self.name, 'at least' if defaults else 'exactly', num_required,
                'arguments' if num_required > 1 else 'argument', num_total))

        return arg2value


class AttributeDescriptor(object):
    """ The AttributeDescriptor serves as a wrapper
        for interface's attributes """

    def __init__(self, attr):
        self.attr = attr
        self.name = attr.name

    def __get__(self, instance, cls):
        ob = instance.__context__
        value = getattr(ob, self.name)

        return self.attr.check_value(ob, value)

    def __set__(self, instance, value):
        ob = instance.__context__

        self.attr.check_value(ob, value)

        # extract original object
        if isinstance(value, BoundInterfaceContract):
            value = value.__context__

        setattr(ob, self.name, value)


class BoundInterfaceContract(object):

    def __init__(self, context, logger):
        self.__context__ = context
        self.__logger__ = logger

    def __setattr__(self, name, value):
        if name in self.__slots__:
            super(BoundInterfaceContract, self).__setattr__(name, value)
        else:
            raise AttributeError(name)


def method_wrapper(element):
    def func(self, *args, **kwargs):
        return element(self.__context__, self.__logger__, *args, **kwargs)

    return func


def construct_class(iface, elements):
    attrs = {'__module__': iface.__module__}
    slots = {'__context__', '__logger__'}

    for name, element in elements.items():
        slots.add(name)
        if isinstance(element, AttributeContract):
            attrs[name] = AttributeDescriptor(element)
        else:
            attrs[name] = method_wrapper(element)

    name = '%sBoundContract' % iface.__name__
    cls = type(name, (BoundInterfaceContract,), attrs)
    cls.__slots__ = tuple(slots)

    return implementer(iface)(cls)
