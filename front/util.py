"""Utils"""

from functools import partial
from contextlib import suppress
from enum import Enum

from i2 import Sig

ignore_import_problems = suppress(ImportError, ModuleNotFoundError)


def named_partial(func, __name__=None, *args, **kwargs):
    """Same as functools.partial, but with a __name__"""
    f = partial(func, *args, **kwargs)
    f.__name__ = __name__ or func.__name__
    return f


def iterable_to_enum(iterable, name='CustomEnum'):
    return Enum(name, {str(kv): kv for kv in iterable})


def inject_enum_annotations(func=None, **enum_list_for_arg):
    """

    :param func:
    :param enum_list_for_arg:
    :return:

    >>> from inspect import signature
    >>> def foo(a, b: int, c='tat'):
    ...     pass
    >>> bar = inject_enum_annotations(foo, b=[1, 2], c='tit for tat'.split())
    >>> str(signature(bar))  # doctest: +SKIP
    '(a, b: front.util.b_enum, c: front.util.c_enum = 'tat')'
    >>> enum = Sig(bar).annotations['b']
    >>> list(enum)
    [<b_enum.1: 1>, <b_enum.2: 2>]
    >>>
    >>> enum = Sig(bar).annotations['c']
    >>> list(enum)
    [<c_enum.tit: 'tit'>, <c_enum.for: 'for'>, <c_enum.tat: 'tat'>]

    You can also use it this way:

    >>> @inject_enum_annotations(b=[1, 2], c='tit for tat'.split())
    ... def foo(a, b: int, c='tat'):
    ...     pass

    """
    if func is None:
        return partial(inject_enum_annotations, **enum_list_for_arg)

    sig = Sig(func)
    sig = sig.ch_annotations(
        **{
            param: iterable_to_enum(enum_list, name=f'{param}_enum')
            for param, enum_list in enum_list_for_arg.items()
        }
    )
    return sig(func)
