"""Signature and mapping utilities shared by the front modules.

Two families live here: signature rewriting (``inject_enum_annotations``,
``annotate_func_arguments``) used to make functions dispatchable by a UI, and
small mapping helpers (``deep_merge``, ``subdict``, ``normalize_map``) used by
the spec compilation.

>>> deep_merge({'a': {'x': 1, 'y': 2}, 'b': 1}, {'a': {'y': 20}, 'c': 3})
{'a': {'x': 1, 'y': 20}, 'b': 1, 'c': 3}
"""

from copy import copy
from operator import attrgetter
from functools import partial
from collections.abc import Iterable, Callable, Mapping
from contextlib import suppress
from enum import Enum
from inspect import Parameter

from i2 import Sig, double_up_as_factory
from i2.wrapper import Ingress, wrap
from i2.signatures import name_of_obj

from front.types import Map

try:
    from i2 import is_not_set
except ImportError:  # older i2: same sentinel, not exported from the root yet
    from i2.deco import NotSet as _NotSet

    def is_not_set(x) -> bool:
        """Return True iff ``x`` is ``i2``'s ``NotSet`` sentinel."""
        return x is _NotSet


def param_default(param):
    """Return ``param.default``, or ``Parameter.empty`` if it is ``i2``'s ``NotSet``.

    ``NotSet`` in a signature means "no value given", not a real default, so UI and
    schema builders must treat that param as required (no prefill, no type inference
    from the default).

    >>> from inspect import Parameter
    >>> from i2.deco import NotSet
    >>> param_default(Parameter('x', Parameter.KEYWORD_ONLY, default=3))
    3
    >>> param_default(Parameter('x', Parameter.KEYWORD_ONLY, default=NotSet))
    <class 'inspect._empty'>
    >>> param_default(Parameter('x', Parameter.KEYWORD_ONLY))
    <class 'inspect._empty'>
    """
    default = param.default
    return Parameter.empty if is_not_set(default) else default


ignore_import_problems = suppress(ImportError, ModuleNotFoundError)


def identity(x):
    """Return ``x`` unchanged."""
    return x


def iterable_to_enum(iterable, name="CustomEnum"):
    """Make an ``Enum`` whose member names are ``str(value)`` for each value of ``iterable``.

    >>> E = iterable_to_enum([1, 'two'])
    >>> list(E)
    [<CustomEnum.1: 1>, <CustomEnum.two: 'two'>]
    >>> E['1'].value
    1
    """
    return Enum(name, {str(kv): kv for kv in iterable})


def subdict(d: Mapping, keys=None):
    """Get a sub-dict of Mapping ``d``, with only those keys that are both in ``keys`` and ``d``.

    Note that the dict will be ordered as ``keys`` are, so can be used for reordering
    a Mapping.

    >>> subdict({'a': 1, 'b': 2, 'c': 3, 'd': 4}, keys=['b', 'a', 'd'])
    {'b': 2, 'a': 1, 'd': 4}
    """
    return {k: d[k] for k in (keys or ()) if k in d}


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
    """Annotate chosen arguments of ``func`` with Enums of their allowed values.

    :param func: function to wrap
    :param extract_enum_value: If True (default), the wrapped function accepts Enum
        members and hands their ``.value`` to ``func``. If False, only the
        annotations change.
    :param enum_list_for_arg: For every argument you want to enumify (i.e. annotate with
        an Enum), the list of enum values you want.
    :return: A wrapped func.

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

    Again, note that the way we need to specify our ``b`` and ``c`` arguments are as
    ``enum`` types, not as the number ``2`` and string ``'tit'``.

    In the following example, we ask for ``extract_enum_value=False`` so that we
    can still use normal inputs (no Enum objects, though ``b`` and ``c`` will
    still be annotated by the Enums.

    Also note in this example that you can use @ to decorate a function at
    definition time.


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
    with_enumed_sig = sig.ch_annotations(
        **{
            param: iterable_to_enum(enum_list, name=f"{param}_enum")
            for param, enum_list in enum_list_for_arg.items()
        }
    )

    if extract_enum_value:
        get_values_of_enums = partial(
            _get_value_attr, keys=list(enum_list_for_arg), val_trans=attrgetter("value")
        )

        dispatched_enums_func = wrap(
            func, ingress=Ingress(func, kwargs_trans=get_values_of_enums)
        )

        dispatched_enums_func.__signature__ = with_enumed_sig

        return with_enumed_sig(dispatched_enums_func)
    else:
        return with_enumed_sig(func)


from i2.signatures import empty
from i2.wrapper import Wrap
from typing import Union, Tuple, Any, Dict
from collections.abc import Callable, Iterable

Annot = Any
AnnotForArgname = Union[dict[str, Annot], Iterable[tuple[str, Annot]]]
AnnotForType = Union[dict[type, Annot], Iterable[tuple[type, Annot]]]


# TODO: Compare to and possibly use i2.io_trans and/or i2.routing_forest.
# Note: A Parameter->annotation function would be more general
#   A Parameter->Parameter function even more general
def annotate_func_arguments(
    func: Callable,
    *,
    ignore_existing_annot: bool = False,
    annot_for_argname: AnnotForArgname = (),
    annot_for_dflt_type: AnnotForType = (),
    dflt_annot: Annot = empty,
):
    """Add annotations to the arguments of ``func``, by argument name or by default-value type.

    :param func: The function whose args we want to annotate
    :param ignore_existing_annot: Set to True to ignore existing annots.
    :param annot_for_argname: Annotation for specific argnames
    :param annot_for_dflt_type: Annotation for specific types. Arg defaults will be
        compared (with ``isinstance(dflt_val, types)``) to types and the annotation
        (value) of the the first matching type (key) will be injected
    :param dflt_annot: Default annotation to use if no match found earlier.
        The default is ``inspect.Parameter.empty``, which means "don't annotate".
        If you want all your params to be annotated no matter what, you might consider
        ``typing.Any``, or in the case of command line interfaces, ``str``.
    :return: A wrapped function with the desired signature changes, if any changes
        need to be made, or the same function untouched if not.

    >>> from inspect import signature
    >>> from functools import partial
    >>> from typing import Any
    >>>
    >>>
    >>> def foo(a, b, c, aa: int=1, bb: int=1.0, cc: int=None, aaa=1, bbb=1.0, ccc=None):
    ...     pass
    ...

    If nothing changes, you just get back the same function:

    >>> assert str(signature(annotate_func_arguments(foo))) == (
    ...     "(a, b, c, "
    ...     "aa: int = 1, bb: int = 1.0, cc: int = None, "
    ...     "aaa=1, bbb=1.0, ccc=None)"
    ... )

    In the following:

    - ``b: str`` through the argname rule, but ``bb`` (as well as ``aa`` and ``bb``)
      didn't change because ``ignore_existing_annot=False`` by default.

    - ``aaa: float`` (even though default is ``1``) and ``ccc: 'NoneAnnot'`` because of
      the ``annot_for_dflt_type`` rules.

    >>> annotator = partial(
    ...     annotate_func_arguments,
    ...     annot_for_argname = {'b': str, 'bb': str},
    ...     # don't confuse following with dict(int=float), which means {'int': float}
    ...     annot_for_dflt_type = {int: float, type(None): 'NoneAnnot'},
    ... )
    >>>
    >>> wrapped_func = annotator(foo)
    >>> assert str(signature(wrapped_func)) == (
    ... "(a, b: str, c, "
    ... "aa: int = 1, bb: int = 1.0, cc: int = None, "
    ... "aaa: float = 1, bbb=1.0, ccc: 'NoneAnnot' = None)"
    ... )

    See in the following what happens if we ask the default annotation to be ``Any`` and
    ``ignore_existing_annot=True``:

    >>> another_annotator = partial(
    ...     annotator,  # use the previous one, but...
    ...     dflt_annot=Any,  # and specify a default annotation
    ...     ignore_existing_annot=True  # now ignore any existing annotations
    ... )
    >>>
    >>> wrapped_func = another_annotator(foo)
    >>> assert str(signature(wrapped_func)) == (
    ... "(a: Any, b: str, c: Any, "
    ... "aa: float = 1, bb: str = 1.0, cc: 'NoneAnnot' = None, "
    ... "aaa: float = 1, bbb: Any = 1.0, ccc: 'NoneAnnot' = None)"
    ... )
    """
    annot_changes = dict(
        _annotate_func_arguments(
            func,
            annot_for_argname=annot_for_argname,
            annot_for_dflt_type=annot_for_dflt_type,
            dflt_annot=dflt_annot,
            ignore_existing_annot=ignore_existing_annot,
        )
    )
    if annot_changes:
        return Wrap(func, Ingress(Sig(func).modified(**annot_changes)))
    else:
        return func


def _annotate_func_arguments(
    func: Callable,
    *,
    annot_for_argname: AnnotForArgname = (),
    annot_for_dflt_type: AnnotForType = (),
    dflt_annot: Annot = empty,
    ignore_existing_annot=False,
):
    """Yield the ``(name, {'annotation': ...})`` changes for ``annotate_func_arguments``."""
    annot_for_argname = dict(annot_for_argname)
    annot_for_dflt_type = dict(annot_for_dflt_type)
    assert all(isinstance(t, str) and str.isidentifier(t) for t in annot_for_argname), (
        f"All keys should be identifier strings. Some were not: {annot_for_argname=}"
    )
    assert all(isinstance(t, type) for t in annot_for_dflt_type), (
        f"All keys should be types. Some were not: {annot_for_dflt_type=}"
    )
    handled_types = tuple(annot_for_dflt_type)

    for name, param in Sig(func).parameters.items():
        if ignore_existing_annot or param.annotation is empty:
            if name in annot_for_argname:
                yield name, {"annotation": annot_for_argname[name]}
            elif isinstance(default := param_default(param), handled_types):
                # NOTE: will yield the first one found
                for type_ in handled_types:
                    if isinstance(default, type_):
                        yield name, {"annotation": annot_for_dflt_type[type_]}
                        break
            else:
                if dflt_annot is not empty:
                    yield name, {"annotation": dflt_annot}


#
# f = annotate_func_arguments(
#     PCA,
#     annot_for_argname=dict(n_components=int, random_state=int),
#     annot_for_type={str: str}
# )
#
# Sig(f)


def get_value(obj, *args, **kwargs):
    """Return ``obj(*args, **kwargs)`` if ``obj`` is callable, else ``obj`` itself.

    >>> get_value(lambda: 3), get_value(3), get_value(lambda a, b: a + b, 1, 2)
    (3, 3, 3)
    """
    return obj(*args, **kwargs) if isinstance(obj, Callable) else obj


def normalize_map(map: Map) -> Mapping:
    """Resolve a ``Map`` (mapping, callable returning one, or None) to a mapping; None gives ``{}``.

    >>> normalize_map(None), normalize_map({'a': 1}), normalize_map(lambda: {'b': 2})
    ({}, {'a': 1}, {'b': 2})
    """
    return get_value(map) or {}


def deep_merge(a: Mapping, b: Mapping):
    """Merge ``b`` into ``a`` recursively (values of ``b`` win), returning a new dict.

    Nested mappings present in both are merged; any other value in ``b`` replaces
    the one in ``a``. Neither input is modified.

    >>> deep_merge({'a': {'x': 1, 'y': 2}, 'b': 1}, {'a': {'y': 20, 'z': 30}, 'c': 3})
    {'a': {'x': 1, 'y': 20, 'z': 30}, 'b': 1, 'c': 3}
    """
    result = dict(a)
    for key, value_b in b.items():
        value_a = a.get(key)
        if isinstance(value_a, Mapping) and isinstance(value_b, Mapping):
            result[key] = deep_merge(value_a, value_b)
        else:
            result[key] = value_b
    return result


def incremental_str_maker(str_format="{:03.f}"):
    """Make a function that will produce a (incrementally) new string at every call."""
    i = 0

    def mk_next_str():
        nonlocal i
        i += 1
        return str_format.format(i)

    return mk_next_str


unnamed_obj = incremental_str_maker(str_format="UnnamedObject{:03.0f}")


def obj_name(func):
    """Get the name of a callable, or make one (``UnnamedObjectNNN``) for lambdas and nameless objects."""
    name = name_of_obj(func)
    if name is None or name == "<lambda>":
        return unnamed_obj()
    return name


def dflt_name_trans(obj):
    """Default display name: ``obj`` (or its name) with underscores as spaces, title-cased.

    >>> dflt_name_trans('my_func_name')
    'My Func Name'
    """
    obj_str = obj if isinstance(obj, str) else obj_name(obj)
    return obj_str.replace("_", " ").title()


def dflt_trans(objs):
    """Default ``obj`` transformation: ensure every object has a ``__name__``, returning a list.

    Objects are passed through ``copy.copy``, which returns functions unchanged, so
    a lambda's ``__name__`` is set on the lambda itself (to an ``UnnamedObjectNNN``
    name).
    """

    def trans(obj):
        trans_obj = copy(obj)
        trans_obj.__name__ = obj_name(obj)
        return trans_obj

    return list(map(trans, objs))
