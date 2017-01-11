CR = '\n'


class ConfigurationError(Exception):
    """ Raised when inappropriate input values are supplied to an API
    method of a :term:`Configurator`"""


class ConfigurationConflictError(ConfigurationError):
    """ Raised when a configuration conflict is detected during action
    processing"""

    def __init__(self, conflicts):
        self._conflicts = conflicts

    def __str__(self):
        r = ["Conflicting configuration actions"]
        items = sorted(self._conflicts.items())
        for discriminator, infos in items:
            r.append("  For: %s" % (discriminator, ))
            for info in infos:
                for line in str(info).rstrip().split(CR):
                    r.append("    " + line)

        return CR.join(r)


class ConfigurationExecutionError(ConfigurationError):
    """An error occurred during execution of a configuration action
    """

    def __init__(self, etype, evalue, info, action=None):
        self.etype, self.evalue, \
            self.info, self.action = etype, evalue, info, action

    def __str__(self):
        return "%s: %s\n  in:\n  %s\n  %s" % (
            self.etype, self.evalue, self.info, self.action)


class CyclicDependencyError(Exception):
    """ The exception raised when the Pyramid topological sorter detects a
    cyclic dependency."""
    def __init__(self, cycles):
        self.cycles = cycles

    def __str__(self):
        L = []
        cycles = self.cycles
        for cycle in cycles:
            dependent = cycle
            dependees = cycles[cycle]
            L.append('%r sorts before %r' % (dependent, dependees))
        msg = 'Implicit ordering cycle:' + '; '.join(L)
        return msg
