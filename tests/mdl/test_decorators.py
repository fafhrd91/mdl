import mdl
import unittest
from zope import interface


class Marker(object):

    def __init__(self, provides):
        interface.directlyProvides(self, provides)


class IMarker1(interface.Interface):
    pass


class IMarker2(interface.Interface):
    pass


def marker_adapter(marker):
    return Marker(IMarker2)


class DecoratorsTestCase(unittest.TestCase):

    def setUp(self):
        self.registry = mdl.Registry()
        self.registry.install()

        self.addCleanup(self.registry.uninstall)

    def test_adapter(self):
        adapter = mdl.adapter(IMarker1, IMarker2)
        adapter(marker_adapter)

        config = mdl.Configurator(registry=self.registry)
        config.scan(__name__)
        config.commit()

        marker = Marker(IMarker1)

        m = self.registry.getAdapter(marker, IMarker2)
        self.assertTrue(IMarker2.providedBy(m))

        m = IMarker2(marker)
        self.assertTrue(IMarker2.providedBy(m))
