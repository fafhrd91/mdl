from __future__ import absolute_import

import sys
from zope.interface.interface import InterfaceClass
from contracts.interface import Contract, ContractNotRespected, describe_type
from contracts.syntax import \
    Combine, Word, W, alphas, alphanums, oneOf, Keyword, ZeroOrMore, S

from ..path import DottedNameResolver

__all__ = ('Reference',)

ID = '__ref_type__'


class Reference(Contract):

    def __init__(self, type_ref, module, where=None):
        Contract.__init__(self, where)

        self.type_ob = None
        self.type_ref = type_ref
        self.module = module
        self.is_iface = False

    def resolve(self):
        if self.type_ob is None:
            resolver = DottedNameResolver(self.module)
            try:
                self.type_ob = resolver.resolve(self.type_ref)
            except ImportError:
                self.type_ob = resolver.resolve(
                    '%s.%s' % (self.module, self.type_ref))

            self.is_iface = isinstance(self.type_ob, InterfaceClass)

        return self.type_ob

    def check_contract(self, context, value, silent):
        type_ob = self.resolve()
        context[ID] = self.type_ob

        if self.is_iface:
            if not type_ob.providedBy(value):
                error = 'Expected implementation of %r, got %s.' % (
                    self.type_ob.__name__, describe_type(value))
                raise ContractNotRespected(
                    contract=self, error=error, value=value, context=context)
        elif not isinstance(value, type_ob):
            error = 'Expected type %r, got %s.' % (
                self.type_ob.__name__, describe_type(value))
            raise ContractNotRespected(
                contract=self, error=error, value=value, context=context)

    def __str__(self):
        return self.type_ref

    def __repr__(self):
        return 'Reference(%r)' % self.type_ref

    @staticmethod
    def parse_action(s, loc, tokens):
        module = None
        try:
            level = 0
            while True:
                level += 1
                locs = sys._getframe(level).f_locals
                if '__interface__' in locs:
                    iface = locs['__interface__']
                    if isinstance(iface, InterfaceClass):
                        module = iface.__module__
                        break
        except:  # pragma: no cover
            pass

        return Reference(tokens['type'], module, W(s, loc))


identifier_expression = Combine(oneOf(list(alphas)) + Word('_' + alphanums))

tp_identifier = Combine(
    identifier_expression -
    ZeroOrMore('.' - identifier_expression))('type')
ref_contract = Keyword('ref') - S('(') - tp_identifier - S(')')

# add_contract(tp_identifier.setParseAction(Reference.parse_action))
# add_keyword('ref')
