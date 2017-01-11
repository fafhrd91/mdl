from contracts.docstring_parsing import parse_annotations
from contracts.docstring_parsing import Arg, DocStringInfo as _DocStringInfo


class DocStringInfo(_DocStringInfo):

    def __init__(self, docstring=None,
                 params=None, returns=None, args=(), exceptions=()):
        super(DocStringInfo, self).__init__(
            docstring=docstring, params=params, returns=returns)

        self.args = args
        self.exceptions = exceptions

    @staticmethod
    def parse(docstring, parse_args=False):
        parsed = _DocStringInfo.parse(docstring)

        _, exc_ann = parse_annotations(docstring, ('exc',), True, False)

        exceptions = []
        for exc_type in exc_ann.values():
            exceptions.append(Arg(exc_type, exc_type))

        args = []

        if parse_args:
            _, args_ann = parse_annotations(docstring, ('type',), True, False)
            for arg_type in args_ann.values():
                args.append(Arg(arg_type, arg_type))

        return DocStringInfo(
            docstring, parsed.params,
            parsed.returns, tuple(args), tuple(exceptions))
