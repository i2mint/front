"""Utils"""

from operator import attrgetter
from functools import partial
from typing import Iterable, Callable
from contextlib import suppress
from enum import Enum

from i2 import Sig, double_up_as_factory
from i2.wrapper import Ingress, wrap

ignore_import_problems = suppress(ImportError, ModuleNotFoundError)


def partialx(func, *args, __name__=None, rm_partialize=False, **kwargs):
    """Same as functools.partial, but with a __name__"""
    f = partial(func, *args, **kwargs)
    if rm_partialize:
        sig = Sig(func)
        partialized = list(
            sig.kwargs_from_args_and_kwargs(args, kwargs, allow_partial=True)
        )
        sig = sig - partialized
        f = sig(partial(f, *args, **kwargs))
    f.__name__ = __name__ or func.__name__
    return f


def iterable_to_enum(iterable, name='CustomEnum'):
    return Enum(name, {str(kv): kv for kv in iterable})


def _get_value_attr(d: dict, keys: Iterable, val_trans: Callable):
    """Return a copy of ``d`` where ``val_trans`` applied to the values of ``keys``.

    Meant to be used with ``functools.partial`` to fix ``val_trans``, and possibly
    ``transform_keys``.

    >>> _get_value_attr({'a': 1, 'b': 2, 'c': 3}, ['a', 'c'], lambda x: x * 10)
    {'a': 10, 'b': 2, 'c': 30}
    """
    return dict(d, **{k: val_trans(d[k]) for k in keys})


@double_up_as_factory
def inject_enum_annotations(func=None, *, extract_enum_value=True, **enum_list_for_arg):
    """

    :param func:
    :param enum_list_for_arg:
    :return:

    >>> from inspect import signature
    >>> def foo(a, b: int, c='tat'):
    ...     return (a + b) * c
    >>> bar = inject_enum_annotations(foo, b=[1, 2], c='tit for tat'.split())
    >>> str(signature(bar))  # doctest: +SKIP
    '(a, b: front.util.b_enum, c: front.util.c_enum = 'tat')'
    >>> b_enum = Sig(bar).annotations['b']
    >>> list(b_enum)
    [<b_enum.1: 1>, <b_enum.2: 2>]
    >>>
    >>> c_enum = Sig(bar).annotations['c']
    >>> list(c_enum)
    [<c_enum.tit: 'tit'>, <c_enum.for: 'for'>, <c_enum.tat: 'tat'>]

    The wrapped bar now accepts enum objects (whose .values will be extracted and
    handed to foo for computation).

    >>> bar(a=2, b=b_enum['2'], c=c_enum.tit)
    'tittittittit'

    You can also use @ to decorate a function at definition time.
    In the following example, we ask for `extract_enum_value=False` so that we
    can still use normal inputs (no Enum objects, though ``b`` and ``c`` will
    still be annotated by the Enums:

    >>> @inject_enum_annotations(
    ...     b=[1, 2], c='tit for tat'.split(), extract_enum_value=False
    ... )
    ... def foo(a, b: int, c='tat'):
    ...     return (a + b) * c
    >>>
    >>> foo(2, 2, 'tit')
    'tittittittit'

    """
    sig = Sig(func)
    sig = sig.ch_annotations(
        **{
            param: iterable_to_enum(enum_list, name=f'{param}_enum')
            for param, enum_list in enum_list_for_arg.items()
        }
    )

    if extract_enum_value:
        get_values_of_enums = partial(
            _get_value_attr, keys=list(enum_list_for_arg), val_trans=attrgetter('value')
        )
        dispatched_enums_func = wrap(
            func, Ingress(func, kwargs_trans=get_values_of_enums)
        )

        return sig(dispatched_enums_func)
    else:
        return sig(func)
