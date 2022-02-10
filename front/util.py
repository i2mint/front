"""Utils"""

from functools import partial
from contextlib import suppress
from enum import Enum

ignore_import_problems = suppress(ImportError, ModuleNotFoundError)


def named_partial(func, __name__=None, *args, **kwargs):
    """Same as functools.partial, but with a __name__"""
    f = partial(func, *args, **kwargs)
    f.__name__ = __name__ or func.__name__
    return f


def iterable_to_enum(iterable, name='CustomEnum'):
    return Enum(name, {str(kv): kv for kv in iterable})

