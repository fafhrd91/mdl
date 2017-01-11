from __future__ import absolute_import

import zope.interface.interface
from zope.interface.adapter import AdapterLookup as _AdapterLookup
from zope.interface.adapter import AdapterRegistry as _AdapterRegistry
from zope.interface.registry import Components, ComponentLookupError

__all__ = ('Registry',)


NO_CONTRACTS = 0
USE_CONTRACTS = 1
USE_CONTRACTS_WARN = 2


class AdapterLookup(_AdapterLookup):

    def lookup(self, required, provided, name=u'', default=None):
        factory = super(AdapterLookup, self).lookup(
            required, provided, name=name, default=default)

        if factory is None or self._registry.level == NO_CONTRACTS:
            return factory

        contract = getattr(provided, '__contract__', None)
        if contract is not None:
            return contract.bind_adapter(factory, self._registry.logger)

        return factory


class AdapterRegistry(_AdapterRegistry):

    level = NO_CONTRACTS
    logger = None
    LookupClass = AdapterLookup

    def __init__(self, bases=(), logger=None):
        self.logger = logger

        super(AdapterRegistry, self).__init__(bases=bases)

    def enable_contracts(self, level):
        self.level = level


class Registry(Components):
    """ Registry """

    def __init__(self, name='', bases=(),
                 use_contracts=NO_CONTRACTS, flavor=None, logger=None):
        self._use_contracts = use_contracts
        self._flavor = flavor
        self._logger = logger

        super(Registry, self).__init__(name, bases)

    def _init_registries(self):
        self.adapters = AdapterRegistry(logger=self._logger)
        self.utilities = AdapterRegistry(logger=self._logger)

    @property
    def flavor(self):
        return self._flavor

    def enable_contracts(self, warn_only=False):
        if warn_only:
            self._use_contracts = USE_CONTRACTS_WARN
            self.adapters.enable_contracts(USE_CONTRACTS_WARN)
        else:
            self._use_contracts = USE_CONTRACTS
            self.adapters.enable_contracts(USE_CONTRACTS)

    def _adapter_hook(self, interface, object, name='', default=None):
        return self.queryAdapter(object, interface, name, default)

    def install(self, use_contracts=False):
        zope.interface.interface.adapter_hooks.append(self._adapter_hook)

        if use_contracts:
            self.enable_contracts()

    def uninstall(self):
        if self._adapter_hook in zope.interface.interface.adapter_hooks:
            zope.interface.interface.adapter_hooks.remove(self._adapter_hook)

    def queryAdapter(self, object, interface, name=u'', default=None):
        if isinstance(object, (tuple, list)):
            adapter = self.adapters.queryMultiAdapter(
                object, interface, name, default)
        else:
            adapter = self.adapters.queryAdapter(
                object, interface, name, default)

        if self._use_contracts == NO_CONTRACTS:
            return adapter

        contract = getattr(interface, 'contract', None)
        if contract and adapter is not None:
            return contract(adapter, logger=self._logger)

        return adapter

    def getAdapter(self, object, interface, name=u''):
        adapter = self.adapters.queryAdapter(object, interface, name)
        if adapter is None:
            raise ComponentLookupError(object, interface, name)

        if self._use_contracts == NO_CONTRACTS:
            return adapter

        contract = getattr(interface, 'contract', None)
        if contract:
            return contract(adapter, logger=self._logger)

        return adapter

    def __enter__(self):
        self.install()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.uninstall()
        return False
