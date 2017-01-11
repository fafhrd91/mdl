import itertools
import os.path
import operator
import six
import sys
import venusian
import pkg_resources

from .interfaces import CATEGORY
from .registry import Registry
from .path import AssetResolver, DottedNameResolver
from .exceptions import ConfigurationError
from .exceptions import ConfigurationConflictError, ConfigurationExecutionError

__all__ = ('Configurator',)


class Configurator(object):

    def __init__(self, loader=None, registry=None, swagger_config=None,
                 flavor=None, debug=False, debug_config=False):
        self._directives = {}
        self.flavor = flavor
        self.resolver = DottedNameResolver()
        self.asset_resolver = AssetResolver()
        self.action_state = ActionState()
        self.scanner = venusian.Scanner(config=self)
        self.packages = set()
        self.debug = debug
        self.debug_config = debug_config
        self.swagger_config = swagger_config

        # set registry
        if registry is None:
            registry = Registry(flavor=flavor)
        self.registry = registry

        # loader
        loader = self.maybe_dotted(loader)
        if callable(loader):
            loader = loader()

        self.loader = loader
        if self.loader:
            self.loader.configure(self, swagger_config)

    def load_mdl_file(self, path):
        if self.loader is None:
            raise ConfigurationError('config loader is not set')

        if os.path.exists(path):
            self.loader.load(open(path).read(), self.flavor)
        else:
            path = self.asset_resolver.resolve(path)
            self.loader.load(open(path.abspath()).read(), self.flavor)

    def load_namespace(self, name):
        if name.endswith('.'):
            namespace = name
        else:
            namespace = '%s.' % name

        files = set()

        def visit(files, dirname, names):
            for name in (name for name in names if name.endswith('.mdl')):
                files.add(os.path.join(dirname, name))

        for dist in pkg_resources.working_set:
            if (dist.project_name == name or
                    dist.project_name.startswith(namespace)):
                os.path.walk(dist.location, visit, files)

        for f in files:
            self.load_mdl_file(f)

    def maybe_dotted(self, dotted):
        return self.resolver.maybe_resolve(dotted)

    def maybe_dotted_seq(self, items):
        if items is None:
            return items

        if not isinstance(items, (tuple, list)):
            items = (items,)

        return tuple(self.maybe_dotted(item) for item in items)

    def action(self, discriminator, callable, order=0):
        if self.debug_config:
            print('Action: %s %s' % (discriminator, callable))
        self.action_state.action(discriminator, callable, order=order)

    def add_directive(self, name, directive):
        self._directives[name] = self.maybe_dotted(directive)

    def __getattr__(self, name):
        # allow directive extension names to work
        c = self._directives.get(name)
        if c is None:
            raise AttributeError(name)

        # Create a bound method (works on both Py2 and Py3)
        # http://stackoverflow.com/a/1015405/209039
        m = c.__get__(self, self.__class__)
        return m

    def add_adapter(self, factory, required, provided=None, name=u''):
        required = self.maybe_dotted_seq(required)
        provided = self.maybe_dotted(provided)
        discriminator = ('adapter', required, provided, name)

        def register():
            self.registry.registerAdapter(
                factory, required=required, provided=provided, name=name)

        self.action(discriminator, register)

    def scan(self, package):
        pkg = self.maybe_dotted(package)
        self.packages.add(pkg)

    def commit(self):
        registry = self.registry
        if self.debug:
            registry.enable_contracts()

        self.scan('mdl')

        if self.loader is not None:
            for pkg in self.loader.packages():
                self.scan(pkg)

        for pkg in self.packages:
            self.scanner.scan(pkg, categories=(CATEGORY,))

        if self.loader is not None:
            self.loader.commit(self)

        self.action_state.execute_actions()

        self.registry = Registry()
        self.action_state = ActionState()

        return registry


# this class is licensed under the ZPL (stolen from Zope)
class ActionState(object):

    def __init__(self):
        # NB "actions" is an API, dep'd upon by pyramid_zcml's load_zcml func
        self.actions = []
        self._seen_files = set()

    def processSpec(self, spec):
        """Check whether a callable needs to be processed.  The ``spec``
        refers to a unique identifier for the callable.

        Return True if processing is needed and False otherwise. If
        the callable needs to be processed, it will be marked as
        processed, assuming that the caller will procces the callable if
        it needs to be processed.
        """
        if spec in self._seen_files:
            return False
        self._seen_files.add(spec)
        return True

    def action(self, discriminator, callable=None, args=(), kw=None, order=0,
               includepath=(), info=None, introspectables=(), **extra):
        """Add an action with the given discriminator, callable and arguments
        """
        if kw is None:
            kw = {}
        action = extra
        action.update(
            dict(
                discriminator=discriminator,
                callable=callable,
                args=args,
                kw=kw,
                includepath=includepath,
                info=info,
                order=order,
                introspectables=introspectables,
            )
        )
        self.actions.append(action)

    def execute_actions(self, clear=True, introspector=None):
        """Execute the configuration actions

        This calls the action callables after resolving conflicts

        For example:

        >>> output = []
        >>> def f(*a, **k):
        ...    output.append(('f', a, k))
        >>> context = ActionState()
        >>> context.actions = [
        ...   (1, f, (1,)),
        ...   (1, f, (11,), {}, ('x', )),
        ...   (2, f, (2,)),
        ...   ]
        >>> context.execute_actions()
        >>> output
        [('f', (1,), {}), ('f', (2,), {})]

        If the action raises an error, we convert it to a
        ConfigurationExecutionError.

        >>> output = []
        >>> def bad():
        ...    bad.xxx
        >>> context.actions = [
        ...   (1, f, (1,)),
        ...   (1, f, (11,), {}, ('x', )),
        ...   (2, f, (2,)),
        ...   (3, bad, (), {}, (), 'oops')
        ...   ]
        >>> try:
        ...    v = context.execute_actions()
        ... except ConfigurationExecutionError, v:
        ...    pass
        >>> print(v)
        exceptions.AttributeError: 'function' object has no attribute 'xxx'
          in:
          oops

        Note that actions executed before the error still have an effect:

        >>> output
        [('f', (1,), {}), ('f', (2,), {})]

        The execution is re-entrant such that actions may be added by other
        actions with the one caveat that the order of any added actions must
        be equal to or larger than the current action.

        >>> output = []
        >>> def f(*a, **k):
        ...   output.append(('f', a, k))
        ...   context.actions.append((3, g, (8,), {}))
        >>> def g(*a, **k):
        ...    output.append(('g', a, k))
        >>> context.actions = [
        ...   (1, f, (1,)),
        ...   ]
        >>> context.execute_actions()
        >>> output
        [('f', (1,), {}), ('g', (8,), {})]

        """
        try:
            all_actions = []
            executed_actions = []
            action_iter = iter([])
            conflict_state = ConflictResolverState()

            while True:
                # We clear the actions list prior to execution so if there
                # are some new actions then we add them to the mix and resolve
                # conflicts again. This orders the new actions as well as
                # ensures that the previously executed actions have no new
                # conflicts.
                if self.actions:
                    all_actions.extend(self.actions)
                    action_iter = resolveConflicts(
                        self.actions,
                        state=conflict_state,
                    )
                    self.actions = []

                action = next(action_iter, None)
                if action is None:
                    # we are done!
                    break

                callable = action['callable']
                args = action['args']
                kw = action['kw']
                info = action['info']
                # we use "get" below in case an action was added via a ZCML
                # directive that did not know about introspectables
                introspectables = action.get('introspectables', ())

                try:
                    if callable is not None:
                        callable(*args, **kw)
                except Exception:
                    t, v, tb = sys.exc_info()
                    try:
                        six.reraise(
                            ConfigurationExecutionError,
                            ConfigurationExecutionError(t, v, info, action),
                            tb)
                    finally:
                        del t, v, tb

                if introspector is not None:
                    for introspectable in introspectables:
                        introspectable.register(introspector, info)

                executed_actions.append(action)

            self.actions = all_actions
            return executed_actions

        finally:
            if clear:
                self.actions = []


class ConflictResolverState(object):
    def __init__(self):
        # keep a set of resolved discriminators to test against to ensure
        # that a new action does not conflict with something already executed
        self.resolved_ainfos = {}

        # actions left over from a previous iteration
        self.remaining_actions = []

        # after executing an action we memoize its order to avoid any new
        # actions sending us backward
        self.min_order = None

        # unique tracks the index of the action so we need it to increase
        # monotonically across invocations to resolveConflicts
        self.start = 0


# this function is licensed under the ZPL (stolen from Zope)
def resolveConflicts(actions, state=None):
    """Resolve conflicting actions

    Given an actions list, identify and try to resolve conflicting actions.
    Actions conflict if they have the same non-None discriminator.

    Conflicting actions can be resolved if the include path of one of
    the actions is a prefix of the includepaths of the other
    conflicting actions and is unequal to the include paths in the
    other conflicting actions.

    Actions are resolved on a per-order basis because some discriminators
    cannot be computed until earlier actions have executed. An action in an
    earlier order may execute successfully only to find out later that it was
    overridden by another action with a smaller include path. This will result
    in a conflict as there is no way to revert the original action.

    ``state`` may be an instance of ``ConflictResolverState`` that
    can be used to resume execution and resolve the new actions against the
    list of executed actions from a previous call.

    """
    if state is None:
        state = ConflictResolverState()

    # pick up where we left off last time, but track the new actions as well
    state.remaining_actions.extend(normalize_actions(actions))
    actions = state.remaining_actions

    def orderandpos(v):
        n, v = v
        return (v['order'] or 0, n)

    def orderonly(v):
        n, v = v
        return v['order'] or 0

    sactions = sorted(enumerate(actions, start=state.start), key=orderandpos)
    for order, actiongroup in itertools.groupby(sactions, orderonly):
        # "order" is an integer grouping. Actions in a lower order will be
        # executed before actions in a higher order.  All of the actions in
        # one grouping will be executed (its callable, if any will be called)
        # before any of the actions in the next.
        output = []
        unique = {}

        # error out if we went backward in order
        if state.min_order is not None and order < state.min_order:
            r = ['Actions were added to order={0} after execution had moved '
                 'on to order={1}. Conflicting actions: '
                 .format(order, state.min_order)]
            for i, action in actiongroup:
                for line in str(action['info']).rstrip().split('\n'):
                    r.append("  " + line)
            raise ConfigurationError('\n'.join(r))

        for i, action in actiongroup:
            # Within an order, actions are executed sequentially based on
            # original action ordering ("i").

            # "ainfo" is a tuple of (i, action) where "i" is an integer
            # expressing the relative position of this action in the action
            # list being resolved, and "action" is an action dictionary.  The
            # purpose of an ainfo is to associate an "i" with a particular
            # action; "i" exists for sorting after conflict resolution.
            ainfo = (i, action)

            # wait to defer discriminators until we are on their order because
            # the discriminator may depend on state from a previous order
            discriminator = action['discriminator']
            action['discriminator'] = discriminator

            if discriminator is None:
                # The discriminator is None, so this action can never conflict.
                # We can add it directly to the result.
                output.append(ainfo)
                continue

            L = unique.setdefault(discriminator, [])
            L.append(ainfo)

        # Check for conflicts
        conflicts = {}
        for discriminator, ainfos in unique.items():
            # We use (includepath, i) as a sort key because we need to
            # sort the actions by the paths so that the shortest path with a
            # given prefix comes first.  The "first" action is the one with the
            # shortest include path.  We break sorting ties using "i".
            def bypath(ainfo):
                path, i = ainfo[1]['includepath'], ainfo[0]
                return path, order, i

            ainfos.sort(key=bypath)
            ainfo, rest = ainfos[0], ainfos[1:]
            _, action = ainfo

            # ensure this new action does not conflict with a previously
            # resolved action from an earlier order / invocation
            prev_ainfo = state.resolved_ainfos.get(discriminator)
            if prev_ainfo is not None:
                _, paction = prev_ainfo
                basepath, baseinfo = paction['includepath'], paction['info']
                includepath = action['includepath']
                # if the new action conflicts with the resolved action then
                # note the conflict, otherwise drop the action as it's
                # effectively overriden by the previous action
                if (includepath[:len(basepath)] != basepath or
                        includepath == basepath):
                    L = conflicts.setdefault(discriminator, [baseinfo])
                    L.append(action['info'])

            else:
                output.append(ainfo)

            basepath, baseinfo = action['includepath'], action['info']
            for _, action in rest:
                includepath = action['includepath']
                # Test whether path is a prefix of opath
                if (includepath[:len(basepath)] != basepath or  # not a prefix
                        includepath == basepath):
                    L = conflicts.setdefault(discriminator, [baseinfo])
                    L.append(action['info'])

        if conflicts:
            raise ConfigurationConflictError(conflicts)

        # sort resolved actions by "i" and yield them one by one
        for i, action in sorted(output, key=operator.itemgetter(0)):
            # do not memoize the order until we resolve an action inside it
            state.min_order = action['order']
            state.start = i + 1
            state.remaining_actions.remove(action)
            state.resolved_ainfos[action['discriminator']] = (i, action)
            yield action


def normalize_actions(actions):
    """Convert old-style tuple actions to new-style dicts."""
    result = []
    for v in actions:
        if not isinstance(v, dict):
            v = expand_action_tuple(*v)
        result.append(v)
    return result


def expand_action_tuple(
    discriminator, callable=None, args=(), kw=None, includepath=(),
    info=None, order=0, introspectables=(),
):
    if kw is None:
        kw = {}
    return dict(
        discriminator=discriminator,
        callable=callable,
        args=args,
        kw=kw,
        includepath=includepath,
        info=info,
        order=order,
        introspectables=introspectables,
    )
