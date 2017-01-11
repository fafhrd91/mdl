import unittest
import os
from six import PY2

here = os.path.abspath(os.path.dirname(__file__))


class TestCallerPath(unittest.TestCase):

    def tearDown(self):
        from tests.mdl import test_path
        if hasattr(test_path, '__abspath__'):
            del test_path.__abspath__

    def _callFUT(self, path, level=2):
        from mdl.path import caller_path
        return caller_path(path, level)

    def test_isabs(self):
        result = self._callFUT('/a/b/c')
        self.assertEqual(result, '/a/b/c')

    def test_pkgrelative(self):
        import os
        result = self._callFUT('a/b/c')
        self.assertEqual(result, os.path.join(here, 'a/b/c'))

    def test_memoization_has_abspath(self):
        import os
        from tests.mdl import test_path
        test_path.__abspath__ = '/foo/bar'
        result = self._callFUT('a/b/c')
        self.assertEqual(result, os.path.join('/foo/bar', 'a/b/c'))

    def test_memoization_success(self):
        import os
        from tests.mdl import test_path
        result = self._callFUT('a/b/c')
        self.assertEqual(result, os.path.join(here, 'a/b/c'))
        self.assertEqual(test_path.__abspath__, here)


class TestCallerModule(unittest.TestCase):

    def _callFUT(self, *arg, **kw):
        from mdl.path import caller_module
        return caller_module(*arg, **kw)

    def test_it_level_1(self):
        from tests.mdl import test_path
        result = self._callFUT(1)
        self.assertEqual(result, test_path)

    def test_it_level_2(self):
        from tests.mdl import test_path
        result = self._callFUT(2)
        self.assertEqual(result, test_path)

    def test_it_level_3(self):
        from tests.mdl import test_path
        result = self._callFUT(3)
        self.assertNotEqual(result, test_path)

    def test_it_no___name__(self):
        class DummyFrame(object):
            f_globals = {}

        class DummySys(object):
            def _getframe(self, level):
                return DummyFrame()
            modules = {'__main__': 'main'}

        dummy_sys = DummySys()
        result = self._callFUT(3, sys=dummy_sys)
        self.assertEqual(result, 'main')


class TestCallerPackage(unittest.TestCase):

    def _callFUT(self, *arg, **kw):
        from mdl.path import caller_package
        return caller_package(*arg, **kw)

    def test_it_level_1(self):
        from tests import mdl
        result = self._callFUT(1)
        self.assertEqual(result, mdl)

    def test_it_level_2(self):
        import tests.mdl
        result = self._callFUT(2)
        self.assertEqual(result, tests.mdl)

    def test_it_level_3(self):
        import unittest
        result = self._callFUT(3)
        self.assertEqual(result, unittest)

    def test_it_package(self):
        import tests

        def dummy_caller_module(*arg):
            return tests

        result = self._callFUT(1, caller_module=dummy_caller_module)
        self.assertEqual(result, tests)


class TestPackagePath(unittest.TestCase):

    def _callFUT(self, package):
        from mdl.path import package_path
        return package_path(package)

    def test_it_package(self):
        import tests
        package = DummyPackageOrModule(tests)
        result = self._callFUT(package)
        self.assertEqual(result, package.package_path)

    def test_it_module(self):
        from tests.mdl import test_path
        module = DummyPackageOrModule(test_path)
        result = self._callFUT(module)
        self.assertEqual(result, module.package_path)

    def test_memoization_success(self):
        from tests.mdl import test_path
        module = DummyPackageOrModule(test_path)
        self._callFUT(module)
        self.assertEqual(module.__abspath__, module.package_path)

    def test_memoization_fail(self):
        from tests.mdl import test_path
        module = DummyPackageOrModule(test_path, raise_exc=TypeError)
        result = self._callFUT(module)
        self.assertFalse(hasattr(module, '__abspath__'))
        self.assertEqual(result, module.package_path)


class TestPackageOf(unittest.TestCase):

    def _callFUT(self, package):
        from mdl.path import package_of
        return package_of(package)

    def test_it_package(self):
        import tests
        package = DummyPackageOrModule(tests)
        result = self._callFUT(package)
        self.assertEqual(result, tests)

    def test_it_module(self):
        import tests.mdl.test_path
        import tests.mdl
        package = DummyPackageOrModule(tests.mdl.test_path)
        result = self._callFUT(package)
        self.assertEqual(result, tests.mdl)


class TestPackageName(unittest.TestCase):

    def _callFUT(self, package):
        from mdl.path import package_name
        return package_name(package)

    def test_it_package(self):
        import tests
        package = DummyPackageOrModule(tests)
        result = self._callFUT(package)
        self.assertEqual(result, 'tests')

    def test_it_namespace_package(self):
        from tests import mdl
        package = DummyNamespacePackage(mdl)
        result = self._callFUT(package)
        self.assertEqual(result, 'tests.mdl')

    def test_it_module(self):
        from tests.mdl import test_path
        module = DummyPackageOrModule(test_path)
        result = self._callFUT(module)
        self.assertEqual(result, 'tests.mdl')

    def test_it_None(self):
        result = self._callFUT(None)
        self.assertEqual(result, '__main__')

    def test_it_main(self):
        import __main__
        result = self._callFUT(__main__)
        self.assertEqual(result, '__main__')


class TestResolver(unittest.TestCase):

    def _getTargetClass(self):
        from mdl.path import Resolver
        return Resolver

    def _makeOne(self, package):
        return self._getTargetClass()(package)

    def test_get_package_caller_package(self):
        import tests
        from mdl.path import CALLER_PACKAGE
        self.assertEqual(
            self._makeOne(CALLER_PACKAGE).get_package(), tests.mdl)

    def test_get_package_name_caller_package(self):
        from mdl.path import CALLER_PACKAGE
        self.assertEqual(
            self._makeOne(CALLER_PACKAGE).get_package_name(), 'tests.mdl')

    def test_get_package_string(self):
        import tests
        self.assertEqual(self._makeOne('tests').get_package(), tests)

    def test_get_package_name_string(self):
        self.assertEqual(self._makeOne('tests').get_package_name(), 'tests')


class TestAssetResolver(unittest.TestCase):
    def _getTargetClass(self):
        from mdl.path import AssetResolver
        return AssetResolver

    def _makeOne(self, package='tests'):
        return self._getTargetClass()(package)

    def test_ctor_as_package(self):
        import sys
        tests = sys.modules['tests']
        inst = self._makeOne(tests)
        self.assertEqual(inst.package, tests)

    def test_ctor_as_str(self):
        import sys
        tests = sys.modules['tests']
        inst = self._makeOne('tests')
        self.assertEqual(inst.package, tests)

    def test_resolve_abspath(self):
        from mdl.path import FSAssetDescriptor
        inst = self._makeOne(None)
        r = inst.resolve(os.path.join(here, 'test_path.py'))
        self.assertEqual(r.__class__, FSAssetDescriptor)
        self.assertTrue(r.exists())

    def test_resolve_absspec(self):
        from mdl.path import PkgResourcesAssetDescriptor
        inst = self._makeOne(None)
        r = inst.resolve('tests.mdl:test_path.py')
        self.assertEqual(r.__class__, PkgResourcesAssetDescriptor)
        self.assertTrue(r.exists())

    def test_resolve_relspec_with_pkg(self):
        from mdl.path import PkgResourcesAssetDescriptor
        inst = self._makeOne('tests.mdl')
        r = inst.resolve('test_path.py')
        self.assertEqual(r.__class__, PkgResourcesAssetDescriptor)
        self.assertTrue(r.exists())

    def test_resolve_relspec_no_package(self):
        inst = self._makeOne(None)
        self.assertRaises(ValueError, inst.resolve, 'test_path.py')

    def test_resolve_relspec_caller_package(self):
        from mdl.path import PkgResourcesAssetDescriptor
        from mdl.path import CALLER_PACKAGE
        inst = self._makeOne(CALLER_PACKAGE)
        r = inst.resolve('test_path.py')
        self.assertEqual(r.__class__, PkgResourcesAssetDescriptor)
        self.assertTrue(r.exists())


class TestPkgResourcesAssetDescriptor(unittest.TestCase):

    def _getTargetClass(self):
        from mdl.path import PkgResourcesAssetDescriptor
        return PkgResourcesAssetDescriptor

    def _makeOne(self, pkg='tests.mdl', path='test_path.py'):
        return self._getTargetClass()(pkg, path)

    def test_absspec(self):
        inst = self._makeOne()
        self.assertEqual(inst.absspec(), 'tests.mdl:test_path.py')

    def test_abspath(self):
        inst = self._makeOne()
        self.assertEqual(inst.abspath(), os.path.join(here, 'test_path.py'))

    def test_stream(self):
        inst = self._makeOne()
        inst.pkg_resources = DummyPkgResource()
        inst.pkg_resources.resource_stream = lambda x, y: '%s:%s' % (x, y)
        s = inst.stream()
        self.assertEqual(
            s, '%s:%s' % ('tests.mdl', 'test_path.py'))

    def test_isdir(self):
        inst = self._makeOne()
        inst.pkg_resources = DummyPkgResource()
        inst.pkg_resources.resource_isdir = lambda x, y: '%s:%s' % (x, y)
        self.assertEqual(inst.isdir(),
                         '%s:%s' % ('tests.mdl', 'test_path.py'))

    def test_listdir(self):
        inst = self._makeOne()
        inst.pkg_resources = DummyPkgResource()
        inst.pkg_resources.resource_listdir = lambda x, y: '%s:%s' % (x, y)
        self.assertEqual(inst.listdir(),
                         '%s:%s' % ('tests.mdl', 'test_path.py'))

    def test_exists(self):
        inst = self._makeOne()
        inst.pkg_resources = DummyPkgResource()
        inst.pkg_resources.resource_exists = lambda x, y: '%s:%s' % (x, y)
        self.assertEqual(inst.exists(),
                         '%s:%s' % ('tests.mdl', 'test_path.py'))


class TestFSAssetDescriptor(unittest.TestCase):
    def _getTargetClass(self):
        from mdl.path import FSAssetDescriptor
        return FSAssetDescriptor

    def _makeOne(self, path=os.path.join(here, 'test_path.py')):
        return self._getTargetClass()(path)

    def test_absspec(self):
        inst = self._makeOne()
        self.assertRaises(NotImplementedError, inst.absspec)

    def test_abspath(self):
        inst = self._makeOne()
        self.assertEqual(inst.abspath(), os.path.join(here, 'test_path.py'))

    def test_stream(self):
        inst = self._makeOne()
        s = inst.stream()
        val = s.read()
        s.close()
        self.assertTrue(b'app' in val)

    def test_isdir_False(self):
        inst = self._makeOne()
        self.assertFalse(inst.isdir())

    def test_isdir_True(self):
        inst = self._makeOne(here)
        self.assertTrue(inst.isdir())

    def test_listdir(self):
        inst = self._makeOne(here)
        self.assertTrue(inst.listdir())

    def test_exists(self):
        inst = self._makeOne()
        self.assertTrue(inst.exists())


class TestDottedNameResolver(unittest.TestCase):

    def _makeOne(self, package=None):
        from mdl.path import DottedNameResolver
        return DottedNameResolver(package)

    def config_exc(self, func, *arg, **kw):
        try:
            func(*arg, **kw)
        except ValueError as e:
            return e
        else:
            raise AssertionError('Invalid not raised')  # pragma: no cover

    def test_zope_dottedname_style_resolve_builtin(self):
        typ = self._makeOne()
        if PY2:
            result = typ._zope_dottedname_style('__builtin__.str', None)
        else:
            result = typ._zope_dottedname_style('builtins.str', None)
        self.assertEqual(result, str)

    def test_zope_dottedname_style_resolve_absolute(self):
        typ = self._makeOne()
        result = typ._zope_dottedname_style(
            'tests.mdl.test_path.TestDottedNameResolver', None)
        self.assertEqual(result, self.__class__)

    def test_zope_dottedname_style_irrresolveable_absolute(self):
        typ = self._makeOne()
        self.assertRaises(ImportError, typ._zope_dottedname_style,
                          'test_path.nonexisting_name', None)

    def test__zope_dottedname_style_resolve_relative(self):
        import tests
        typ = self._makeOne()
        result = typ._zope_dottedname_style(
            '.mdl.test_path.TestDottedNameResolver', tests)
        self.assertEqual(result, self.__class__)

    def test__zope_dottedname_style_resolve_relative_leading_dots(self):
        import tests.mdl.test_path
        typ = self._makeOne()
        result = typ._zope_dottedname_style(
            '..tests.mdl.test_path.TestDottedNameResolver', tests)
        self.assertEqual(result, self.__class__)

    def test__zope_dottedname_style_resolve_relative_is_dot(self):
        import tests
        typ = self._makeOne()
        result = typ._zope_dottedname_style('.', tests)
        self.assertEqual(result, tests)

    def test__zope_dottedname_style_irresolveable_relative_is_dot(self):
        typ = self._makeOne()
        e = self.config_exc(typ._zope_dottedname_style, '.', None)
        self.assertEqual(
            e.args[0],
            "relative name '.' irresolveable without package")

    def test_zope_dottedname_style_resolve_relative_nocurrentpackage(self):
        typ = self._makeOne()
        e = self.config_exc(typ._zope_dottedname_style, '.whatever', None)
        self.assertEqual(
            e.args[0],
            "relative name '.whatever' irresolveable without package")

    def test_zope_dottedname_style_irrresolveable_relative(self):
        import tests
        typ = self._makeOne()
        self.assertRaises(ImportError, typ._zope_dottedname_style,
                          '.notexisting', tests)

    def test__zope_dottedname_style_resolveable_relative(self):
        import mdl
        typ = self._makeOne()
        result = typ._zope_dottedname_style('.config', mdl)
        from mdl import config
        self.assertEqual(result, config)

    def test__zope_dottedname_style_irresolveable_absolute(self):
        typ = self._makeOne()
        self.assertRaises(
            ImportError,
            typ._zope_dottedname_style, 'tests.fudge.bar', None)

    def test__zope_dottedname_style_resolveable_absolute(self):
        typ = self._makeOne()
        result = typ._zope_dottedname_style(
            'tests.mdl.test_path.TestDottedNameResolver', None)
        self.assertEqual(result, self.__class__)

    def test__pkg_resources_style_resolve_absolute(self):
        typ = self._makeOne()
        result = typ._pkg_resources_style(
            'tests.mdl.test_path:TestDottedNameResolver', None)
        self.assertEqual(result, self.__class__)

    def test__pkg_resources_style_irrresolveable_absolute(self):
        typ = self._makeOne()
        self.assertRaises(ImportError, typ._pkg_resources_style,
                          'tests:nonexisting', None)

    def test__pkg_resources_style_resolve_relative(self):
        import tests
        typ = self._makeOne()
        result = typ._pkg_resources_style(
            '.mdl.test_path:TestDottedNameResolver', tests)
        self.assertEqual(result, self.__class__)

    def test__pkg_resources_style_resolve_relative_is_dot(self):
        import tests
        typ = self._makeOne()
        result = typ._pkg_resources_style('.', tests)
        self.assertEqual(result, tests)

    def test__pkg_resources_style_resolve_relative_nocurrentpackage(self):
        typ = self._makeOne()
        self.assertRaises(ValueError, typ._pkg_resources_style,
                          '.whatever', None)

    def test__pkg_resources_style_irrresolveable_relative(self):
        import mdl
        typ = self._makeOne()
        self.assertRaises(ImportError, typ._pkg_resources_style,
                          ':notexisting', mdl)

    def test_resolve_not_a_string(self):
        typ = self._makeOne()
        e = self.config_exc(typ.resolve, None)
        self.assertEqual(e.args[0], 'None is not a string')

    def test_resolve_using_pkgresources_style(self):
        typ = self._makeOne()
        result = typ.resolve(
            'tests.mdl.test_path:TestDottedNameResolver')
        self.assertEqual(result, self.__class__)

    def test_resolve_using_zope_dottedname_style(self):
        typ = self._makeOne()
        result = typ.resolve(
            'tests.mdl.test_path:TestDottedNameResolver')
        self.assertEqual(result, self.__class__)

    def test_resolve_missing_raises(self):
        typ = self._makeOne()
        self.assertRaises(ImportError, typ.resolve, 'cant.be.found')

    def test_resolve_caller_package(self):
        from mdl.path import CALLER_PACKAGE
        typ = self._makeOne(CALLER_PACKAGE)
        self.assertEqual(typ.resolve('.test_path.TestDottedNameResolver'),
                         self.__class__)

    def test_maybe_resolve_caller_package(self):
        from mdl.path import CALLER_PACKAGE
        typ = self._makeOne(CALLER_PACKAGE)
        self.assertEqual(
            typ.maybe_resolve('.test_path.TestDottedNameResolver'),
            self.__class__)

    def test_ctor_string_module_resolveable(self):
        import tests.mdl
        typ = self._makeOne('tests.mdl.test_path')
        self.assertEqual(typ.package, tests.mdl)

    def test_ctor_string_package_resolveable(self):
        import tests
        typ = self._makeOne('tests')
        self.assertEqual(typ.package, tests)

    def test_ctor_string_irresolveable(self):
        self.assertRaises(ValueError, self._makeOne, 'cant.be.found')

    def test_ctor_module(self):
        import tests.mdl
        import tests.mdl.test_path
        typ = self._makeOne(tests.mdl)
        self.assertEqual(typ.package, tests.mdl)

    def test_ctor_package(self):
        import tests
        typ = self._makeOne(tests)
        self.assertEqual(typ.package, tests)

    def test_ctor_None(self):
        typ = self._makeOne(None)
        self.assertEqual(typ.package, None)


class DummyPkgResource(object):
    pass


class DummyPackageOrModule:

    def __init__(self, real_package_or_module, raise_exc=None):
        self.__dict__['raise_exc'] = raise_exc
        self.__dict__['__name__'] = real_package_or_module.__name__
        import os
        self.__dict__['package_path'] = os.path.dirname(
            os.path.abspath(real_package_or_module.__file__))
        self.__dict__['__file__'] = real_package_or_module.__file__

    def __setattr__(self, key, val):
        if self.raise_exc is not None:
            raise self.raise_exc
        self.__dict__[key] = val


class DummyNamespacePackage:
    """Has no __file__ attribute."""

    def __init__(self, real_package_or_module):
        self.__name__ = real_package_or_module.__name__
        import os
        self.package_path = os.path.dirname(
            os.path.abspath(real_package_or_module.__file__))
