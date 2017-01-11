import collections
import yaml
from six import string_types
from bravado_core.spec import Spec

from . import exceptions

__all__ = ('Loader',)


ApplicationInfo = collections.namedtuple(
    'ApplicationInfo',
    'name base_path in_transform out_transform errors')

OperationInfo = collections.namedtuple(
    'OperationInfo', 'id path method transform errors')


class Loader(object):

    def __init__(self):
        self._apps = []
        self._packages = set()
        self._formats = []

    def configure(self, config, swagger_config):
        self._swagger_config = swagger_config

    def register_format(self, format):
        self._formats.append(format)

    def load(self, s, flavor=None, name=None):
        data = yaml.load(s)

        if flavor is not None:
            fv = data.get('flavor')
            if fv is not None and flavor != fv:
                print('Flavor does not match %s<>%s skip: %s' % (
                    flavor, fv, name))
                return

        # extract package
        package = data.get('x-mdl-package', ())
        if isinstance(package, string_types):
            package = (package,)

        self._packages.update(package)
        self._apps.append(data)

        return data

    def packages(self):
        return self._packages

    def commit(self, config):
        for data in self._apps:
            spec = Spec(data, config=self._swagger_config)
            for format in self._formats:
                spec.register_format(format)

            spec.build()

            app_info = ApplicationInfo(
                data.get('x-mdl-name', ''),
                data.get('basePath', '').rstrip('/'),
                self._seq_of_strings(data.get('x-mdl-middleware')),
                self._seq_of_strings(data.get('x-mdl-middleware')),
                self._dict_from_list(data, 'x-mdl-errors'))

            self.create_app(spec, app_info, config)

            for resource in spec.resources.values():
                self.create_resource(resource, app_info, config)

                for op in resource.operations.values():
                    op_info = OperationInfo(
                        op.operation_id,
                        op.path_name,
                        op.http_method,
                        self._seq_of_strings(op.op_spec.get('x-mdl-handler')),
                        self._dict_from_list(op.op_spec, 'x-mdl-errors'))

                    self.create_operation(op, app_info, op_info, config)

    def create_app(self, spec, app_info, config):
        raise NotImplementedError  # pragma: no cover

    def create_resource(self, resource, app_info, config):
        pass

    def create_operation(self, op, app_info, op_info, config):
        raise NotImplementedError  # pragma: no cover

    def _dict_from_list(self, data, name):
        d = data.get(name)
        if d is None:
            return {}
        if isinstance(d, (tuple, list)):
            data = {}
            for item in d:
                data.update(item)
            return data
        if not isinstance(d, dict):
            raise exceptions.ConfigurationError(
                'dict or None is required for "%s" got %r' % (name, d))
        return d

    def _seq_of_strings(self, s):
        if isinstance(s, string_types):
            return (s,)
        elif s is None:
            return ()
        return s
