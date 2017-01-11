from __future__ import absolute_import
from contracts import syntax

from .extension import tp_identifier, Reference


def reset():
    tp_contract = tp_identifier.setParseAction(Reference.parse_action)

    syntax.hardwired = syntax.MatchFirst(syntax.ParsingTmp.contract_types)
    syntax.hardwired.setName('Predefined contract expression')

    syntax.simple_contract << (syntax.hardwired |
                               syntax.identifier_contract | tp_contract)
    syntax.simple_contract.setName('simple contract expression')

    syntax.any_contract = syntax.composite_contract | syntax.simple_contract
    syntax.any_contract.setName('Any simple or composite contract')
    syntax.contract_expression << (syntax.any_contract)
