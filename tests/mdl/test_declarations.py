import unittest

import mdl
from mdl.declarations import implements


class DeclarationsTests(unittest.TestCase):

    def test_implements(self):

        class I1(mdl.Interface):
            pass

        class C:
            implements(I1)

        ob = C()
        self.assertTrue(I1.providedBy(ob))

        class C2(C):
            pass

        ob2 = C2()
        self.assertTrue(I1.providedBy(ob2))

        class C2:
            implements(I1)

        self.assertTrue(mdl.verifyClass(I1, C2))
        self.assertTrue(I1.implementedBy(C2))
