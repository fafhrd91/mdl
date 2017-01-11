import unittest
import mdl


class Loader(mdl.Loader):
    pass


class ConfiguratorTestCase(unittest.TestCase):

    def test_ctor(self):
        loader = Loader()
        cfg = mdl.Configurator(loader)
        self.assertIsNotNone(cfg.registry)
        self.assertIs(cfg.loader, loader)

        cfg = mdl.Configurator('tests.mdl.test_config.Loader')
        self.assertIsInstance(cfg.loader, Loader)
