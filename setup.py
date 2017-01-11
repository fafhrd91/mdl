#!/usr/bin/env python
import codecs
import os
import re
from setuptools import setup

with codecs.open(os.path.join(os.path.abspath(os.path.dirname(
        __file__)), 'mdl', '__init__.py'), 'r', 'latin1') as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')


def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()


install_requires = [
    'PyYAML', 'PyContracts',
    'bravado_core', 'six', 'zope.interface', 'venusian']

tests_require = install_requires + []


setup(
    name='mdl',
    version=version,
    description='server application composition library',
    long_description='\n\n'.join((read('README.rst'), read('CHANGES.rst'))),
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Development Status :: 5 - Production/Stable',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Internet :: WWW/HTTP'],
    author='Nikolay Kim',
    author_email='fafhrd91@gmail.com',
    url='https://github.com/aio-libs/mdl/',
    license='Apache 2',
    packages=['mdl'],
    install_requires=install_requires,
    tests_require=tests_require,
    include_package_data=True,
)
