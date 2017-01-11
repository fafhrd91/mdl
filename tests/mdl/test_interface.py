import unittest
from zope import interface
from zope.interface.interface import InterfaceClass

import mdl
from mdl import contracts, verify


class CustomModel(object):
    pass


class InterfaceTestCase(unittest.TestCase):

    def test_interface(self):

        def gen_iface():
            class ITest(mdl.Interface):
                def method(a, b, c):
                    """ method

                    :type a: int
                    :type b: str
                    :type c: tests.mdl.test_contracts.CustomModel|None
                    :rtype: int
                    """

            return ITest

        iface = gen_iface()
        self.assertEqual(iface.__name__, 'ITest')
        self.assertIsInstance(iface, InterfaceClass)
        self.assertIsInstance(iface.__contract__, contracts.InterfaceContract)

    def test_require_docstring_contract(self):

        def gen_iface():
            class ITest(mdl.Interface):
                def method(a, b, c):
                    """ method """

        with self.assertRaises(contracts.ContractException):
            gen_iface()

    def test_kwargs(self):

        def gen_iface():
            class ITest(mdl.Interface):
                def method(a, **kwargs):
                    """
                    :type a: int
                    :rtype: int
                    """

        with self.assertRaises(contracts.ContractException):
            gen_iface()

    def test_varargs(self):

        def gen_iface():
            class ITest(mdl.Interface):
                def method(a, *args):
                    """
                    :type a: int
                    :rtype: int
                    """

        with self.assertRaises(contracts.ContractException):
            gen_iface()

    def test_no_attr_spec(self):

        def gen_iface():
            class ITest(mdl.Interface):
                attr = mdl.Attribute('attr', spec='')

        with self.assertRaises(contracts.ContractException):
            gen_iface()

    def test_attr_spec_not_string(self):

        def gen_iface():
            class ITest(mdl.Interface):
                attr = mdl.Attribute('attr', spec=1)

        with self.assertRaises(contracts.ContractException):
            gen_iface()

    def test_verify(self):
        class ITest(mdl.Interface):
            attr = mdl.Attribute('attr', spec='int')

            def method(a):
                """
                :type a: int
                :rtype:None"""

        class Test(object):
            pass

        with self.assertRaises(verify.DoesNotImplement):
            verify.verifyClass(ITest, Test)

        @interface.implementer(ITest)
        class Test2(object):
            pass

        with self.assertRaises(verify.BrokenImplementation):
            verify.verifyClass(ITest, Test2)

        @interface.implementer(ITest)
        class Test3(object):
            def method(self):
                pass

        with self.assertRaises(verify.BrokenMethodImplementation):
            verify.verifyClass(ITest, Test3)

        test = Test3()
        test.method = object()

        with self.assertRaises(verify.DoesNotImplement):
            verify.verifyObject(ITest, object())

        with self.assertRaises(verify.BrokenImplementation):
            ob = Test3()
            ob.method = lambda a: a
            verify.verifyObject(ITest, ob)

        test.attr = 1
        with self.assertRaises(verify.BrokenMethodImplementation):
            verify.verifyObject(ITest, test)

    def test_match_contract_with_default_value(self):

        def gen_iface():
            class ITest(mdl.Interface):
                def method(a=None):
                    """
                    :type a: int
                    """

        with self.assertRaises(contracts.ContractException):
            gen_iface()

    def test_adapter_contract(self):

        class ITest(mdl.Interface):
            """ Test component

            :type: int
            :type: str
            """

        @interface.implementer(ITest)
        class Content(object):
            pass

        def test_adapter(val1, val2):
            return Content()

        config = mdl.Configurator(debug=True)
        config.add_adapter(test_adapter, (int, str), ITest)

        with config.commit():
            res = ITest(1, '123')
            self.assertTrue(ITest.providedBy(res))

        # check result
        def test_adapter2(val1, val2):
            return object()

        config = mdl.Configurator(debug=True)
        config.add_adapter(test_adapter2, (int, str), ITest)

        with config.commit():
            with self.assertRaises(mdl.contracts.ContractException):
                ITest(1, '123')
