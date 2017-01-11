import unittest
from zope import interface
from zope.interface.exceptions import DoesNotImplement
try:
    from unittest import mock
except:
    import mock

import mdl
from mdl import contracts
from mdl.contracts.parser import parse_iface_contract
from mdl.verify import verifyObject


class CustomModel(object):
    pass


class CustomException(Exception):
    pass


class IModel(mdl.Interface):
    """ """


class ContractsTestCase(unittest.TestCase):

    def test_iface_contract_object(self):

        class ITest(interface.Interface):

            attr = mdl.Attribute('attr', spec='int')

            def method(a, b, c):
                """ method

                :type a: int
                :type b: str
                :type c: tests.mdl.test_contracts.CustomModel
                :rtype: int
                """

            def method2(a, c=CustomModel()):
                """ method2

                :type a: str
                :type c: CustomModel
                :rtype: None
                """

        contract = parse_iface_contract(ITest)

        @interface.implementer(ITest)
        class BrokenContract(object):

            attr = 2

            def method(self, a, b, c):
                return 1

            def method2(self, a, c=1):
                pass

        ob = BrokenContract()
        bound = contract.bind(ob)

        with self.assertRaises(contracts.ContractNotRespected):
            bound.method('s1', 's2', CustomModel())

        # check model contract
        with self.assertRaises(contracts.ContractNotRespected):
            bound.method(1, 's2', object())

        # check interface module level model
        with self.assertRaises(contracts.ContractNotRespected):
            bound.method2('s', object())

        result = bound.method(1, 's2', CustomModel())
        self.assertIsInstance(result, int)

        result = bound.method2('s', CustomModel())
        self.assertIsNone(result, int)

        # attribute error
        with self.assertRaises(AttributeError):
            bound.unknown

        with self.assertRaises(AttributeError):
            bound.unknown = 'test'

        # attr
        with self.assertRaises(contracts.ContractNotRespected):
            bound.attr = 'test'

        bound.attr = 109
        self.assertEqual(bound.attr, 109)

    def test_composite_reference(self):

        class ITest(mdl.Interface):
            def method(a):
                """
                :type a: tests.mdl.test_contracts.CustomModel | None
                :rtype: int
                """

        @interface.implementer(ITest)
        class Content(object):
            def method(self, a):
                return 1

        ob = Content()
        bound = ITest.contract(ob)

        self.assertEqual(bound.method(CustomModel()), 1)
        self.assertEqual(bound.method(None), 1)

        with self.assertRaises(contracts.ContractNotRespected):
            bound.method(object())

    def test_verify(self):

        class ITest(mdl.Interface):
            pass

        class Content(object):
            pass

        with self.assertRaises(DoesNotImplement):
            ITest.contract(Content())

    def test_result(self):

        class ITest(mdl.Interface):
            def method1():
                """
                :rtype: int
                """

            def method2():
                """
                :rtype: None
                """

        @interface.implementer(ITest)
        class Content(object):
            def method1(self):
                return 's'

            def method2(self):
                return 100

        ob = Content()
        bound = ITest.contract(ob)

        with self.assertRaises(contracts.ContractNotRespected):
            bound.method1()

        with self.assertRaises(contracts.ContractNotRespected):
            bound.method2()

    def test_contract_signatures(self):

        class ITest(mdl.Interface):

            def method(a, c=1, d='f'):
                """
                :type a: str
                :type c: int
                :type d: str
                :rtype: *
                """

            def method2():
                """:rtype: *"""

        @interface.implementer(ITest)
        class Content(object):
            def method(self, a, c=1, d='f'):
                return (a, c, d)

            def method2(self):
                pass

        ob = ITest.contract(Content())
        self.assertEqual(ob.method('s'), ('s', 1, 'f'))
        self.assertEqual(ob.method('s', 2), ('s', 2, 'f'))
        self.assertEqual(ob.method('s', 2, 'f1'), ('s', 2, 'f1'))
        self.assertEqual(ob.method('s', c=2), ('s', 2, 'f'))
        self.assertEqual(ob.method('s', c=2, d='f1'), ('s', 2, 'f1'))
        self.assertEqual(ob.method('s', d='f2', c=3), ('s', 3, 'f2'))
        self.assertEqual(ob.method(*('s', 3, 'f2')), ('s', 3, 'f2'))

        with self.assertRaises(TypeError):
            ob.method()

        with self.assertRaises(TypeError):
            ob.method2(1)

        with self.assertRaises(TypeError):
            ob.method('s', unknown='test')

        with self.assertRaises(TypeError):
            ob.method('s', 2, 's', 1)

        with self.assertRaises(TypeError):
            ob.method('s', 2, c=10)

    def test_interface_reference(self):

        class ITest(mdl.Interface):
            def method(a):
                """
                :type a: tests.mdl.test_contracts.IModel
                :rtype: tests.mdl.test_contracts.IModel
                """

        @interface.implementer(ITest)
        class Content(object):
            def method(self, a):
                return a

        ob = ITest.contract(Content())

        with self.assertRaises(contracts.ContractNotRespected):
            ob.method(object())

        mod = CustomModel()
        mdl.directlyProvides(mod, IModel)

        self.assertIs(ob.method(mod).__context__, mod)

    def test_contract(self):
        from mdl.contracts.contract import InterfaceContract
        from mdl.contracts.contract import BoundInterfaceContract

        class ITest(mdl.Interface):
            def method(a):
                """
                :type a: tests.mdl.test_contracts.IModel
                :rtype: tests.mdl.test_contracts.IModel
                """

        @interface.implementer(ITest)
        class Content(object):
            def method(self, a):
                return a

        self.assertIsInstance(ITest.__contract__, InterfaceContract)

        ob = ITest.contract(Content())

        verifyObject(ITest, ob)
        self.assertTrue(ITest.providedBy(ob))
        self.assertEqual(ob.__class__.__name__, 'ITestBoundContract')
        self.assertEqual(ob.__module__, 'tests.mdl.test_contracts')

        mod = CustomModel()
        mdl.directlyProvides(mod, IModel)

        bound_mod = IModel.contract(mod)
        self.assertTrue(IModel.providedBy(bound_mod))

        self.assertIsInstance(ob.method(mod), BoundInterfaceContract)
        self.assertIs(ob.method(bound_mod), bound_mod)

    def test_contract_transforms(self):
        from mdl.contracts.contract import BoundInterfaceContract

        class ITest(mdl.Interface):
            attr = mdl.Attribute(
                'attr', spec='tests.mdl.test_contracts.IModel')

        @interface.implementer(ITest)
        class Content(object):
            attr = None

        ob = Content()
        bound = ITest.contract(ob)

        mod = CustomModel()
        mdl.directlyProvides(mod, IModel)

        bound.attr = mod
        self.assertIs(ob.attr, mod)

        bound.attr = IModel.contract(mod)
        self.assertIs(ob.attr, mod)

        self.assertIsInstance(bound.attr, BoundInterfaceContract)

    def test_method_exceptions(self):

        class ITest(mdl.Interface):
            def method():
                """
                :rtype: None
                :exc: tests.mdl.test_contracts.CustomException
                """

        @interface.implementer(ITest)
        class Content(object):
            def method(self):
                raise CustomException()

        logger = mock.Mock()
        ob = ITest.contract(Content(), logger=logger)

        with self.assertRaises(CustomException):
            ob.method()

        self.assertFalse(logger.exception.called)

    def test_method_undefined_exceptions(self):

        class ITest(mdl.Interface):
            def method():
                """
                :rtype: None
                :exc: tests.mdl.test_contracts.CustomException
                """

        @interface.implementer(ITest)
        class Content(object):
            def method(self):
                raise ValueError()

        logger = mock.Mock()
        ob = ITest.contract(Content(), logger=logger)

        with self.assertRaises(ValueError):
            ob.method()

        self.assertEqual(len(logger.exception.call_args_list), 1)
        self.assertEqual(
            logger.exception.call_args_list[0][0][0],
            'Un-defined exception received from ITest.method(...)')
