import os
import six
import yaml
from ..config import Configurator
from ..loader import Loader
from ..path import AssetResolver

__all__ = ('bootstrap', 'bootstrap_with')


def bootstrap(config_path, debug=False):
    if os.path.exists(config_path):
        path = config_path
    else:
        path = AssetResolver().resolve(config_path).abspath()

    with open(path) as f:
        params = yaml.load(f.read())

    flavor = params.get('flavor')
    namespace = params.get('namespace')
    loader = params.get('loader', Loader)
    packages = params.get('packages')

    return bootstrap_with(
        namespace, loader, packages, flavor=flavor, debug=debug)


def bootstrap_with(namespace, loader=Loader,
                   packages=None, flavor=None, debug=False):
    config = Configurator(loader, flavor=flavor, debug=debug)
    if namespace:
        config.load_namespace(namespace)

    # scan packages
    if isinstance(packages, six.string_types):
        packages = (packages,)

    if packages:
        for package in packages:
            config.scan(package)

    return config
