# front.util

Signature and mapping utilities shared by the front modules.

Two families live here: signature rewriting (`inject_enum_annotations`,
`annotate_func_arguments`) used to make functions dispatchable by a UI, and
small mapping helpers (`deep_merge`, `subdict`, `normalize_map`) used by
the spec compilation.

```pycon
>>> deep_merge({'a': {'x': 1, 'y': 2}, 'b': 1}, {'a': {'y': 20}, 'c': 3})
{'a': {'x': 1, 'y': 20}, 'b': 1, 'c': 3}
```

### Functions

| [`annotate_func_arguments`](#front.util.annotate_func_arguments)(func, \*[, ...])   | Add annotations to the arguments of `func`, by argument name or by default-value type.         |
|---------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| [`deep_merge`](#front.util.deep_merge)(a, b)                           | Merge `b` into `a` recursively (values of `b` win), returning a new dict.                      |
| [`dflt_name_trans`](#front.util.dflt_name_trans)(obj)                       | Default display name: `obj` (or its name) with underscores as spaces, title-cased.             |
| [`dflt_trans`](#front.util.dflt_trans)(objs)                           | Default `obj` transformation: ensure every object has a `__name__`, returning a list.          |
| [`get_value`](#front.util.get_value)(obj, \*args, \*\*kwargs)         | Return `obj(*args, **kwargs)` if `obj` is callable, else `obj` itself.                         |
| [`identity`](#front.util.identity)(x)                                | Return `x` unchanged.                                                                          |
| [`incremental_str_maker`](#front.util.incremental_str_maker)([str_format])        | Make a function that will produce a (incrementally) new string at every call.                  |
| `inject_enum_annotations`([func, ...])                                                      | Annotate chosen arguments of `func` with Enums of their allowed values.                        |
| [`iterable_to_enum`](#front.util.iterable_to_enum)(iterable[, name])         | Make an `Enum` whose member names are `str(value)` for each value of `iterable`.               |
| [`normalize_map`](#front.util.normalize_map)(map)                         | Resolve a `Map` (mapping, callable returning one, or None) to a mapping; None gives `{}`.      |
| [`obj_name`](#front.util.obj_name)(func)                             | Get the name of a callable, or make one (`UnnamedObjectNNN`) for lambdas and nameless objects. |
| [`subdict`](#front.util.subdict)(d[, keys])                         | Get a sub-dict of Mapping `d`, with only those keys that are both in `keys` and `d`.           |
| `unnamed_obj`()                                                                             |                                                                                                |

### front.util.annotate_func_arguments(func, , ignore_existing_annot=False, annot_for_argname=(), annot_for_dflt_type=(), dflt_annot)

Add annotations to the arguments of `func`, by argument name or by default-value type.

* **Parameters:**
  * **func** ([`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)) – The function whose args we want to annotate
  * **ignore_existing_annot** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Set to True to ignore existing annots.
  * **annot_for_argname** (`Union`[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)], [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]]) – Annotation for specific argnames
  * **annot_for_dflt_type** (`Union`[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`type`](https://docs.python.org/3/builtins/functions.html#type), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)], [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`type`](https://docs.python.org/3/builtins/functions.html#type), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]]) – Annotation for specific types. Arg defaults will be
    compared (with `isinstance(dflt_val, types)`) to types and the annotation
    (value) of the the first matching type (key) will be injected
  * **dflt_annot** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – Default annotation to use if no match found earlier.
    The default is `inspect.Parameter.empty`, which means “don’t annotate”.
    If you want all your params to be annotated no matter what, you might consider
    `typing.Any`, or in the case of command line interfaces, `str`.
* **Returns:**
  A wrapped function with the desired signature changes, if any changes
  need to be made, or the same function untouched if not.

```pycon
>>> from inspect import signature
>>> from functools import partial
>>> from typing import Any
>>>
>>>
>>> def foo(a, b, c, aa: int=1, bb: int=1.0, cc: int=None, aaa=1, bbb=1.0, ccc=None):
...     pass
...
```

If nothing changes, you just get back the same function:

```pycon
>>> assert str(signature(annotate_func_arguments(foo))) == (
...     "(a, b, c, "
...     "aa: int = 1, bb: int = 1.0, cc: int = None, "
...     "aaa=1, bbb=1.0, ccc=None)"
... )
```

In the following:

- `b: str` through the argname rule, but `bb` (as well as `aa` and `bb`)
  didn’t change because `ignore_existing_annot=False` by default.
- `aaa: float` (even though default is `1`) and `ccc: 'NoneAnnot'` because of
  the `annot_for_dflt_type` rules.

```pycon
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
```

See in the following what happens if we ask the default annotation to be `Any` and
`ignore_existing_annot=True`:

```pycon
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
```

### front.util.deep_merge(a, b)

Merge `b` into `a` recursively (values of `b` win), returning a new dict.

Nested mappings present in both are merged; any other value in `b` replaces
the one in `a`. Neither input is modified.

```pycon
>>> deep_merge({'a': {'x': 1, 'y': 2}, 'b': 1}, {'a': {'y': 20, 'z': 30}, 'c': 3})
{'a': {'x': 1, 'y': 20, 'z': 30}, 'b': 1, 'c': 3}
```

### front.util.dflt_name_trans(obj)

Default display name: `obj` (or its name) with underscores as spaces, title-cased.

```pycon
>>> dflt_name_trans('my_func_name')
'My Func Name'
```

### front.util.dflt_trans(objs)

Default `obj` transformation: ensure every object has a `__name__`, returning a list.

Objects are passed through `copy.copy`, which returns functions unchanged, so
a lambda’s `__name__` is set on the lambda itself (to an `UnnamedObjectNNN`
name).

### front.util.get_value(obj, \*args, \*\*kwargs)

Return `obj(*args, **kwargs)` if `obj` is callable, else `obj` itself.

```pycon
>>> get_value(lambda: 3), get_value(3), get_value(lambda a, b: a + b, 1, 2)
(3, 3, 3)
```

### front.util.identity(x)

Return `x` unchanged.

### front.util.incremental_str_maker(str_format='{:03.f}')

Make a function that will produce a (incrementally) new string at every call.

### front.util.iterable_to_enum(iterable, name='CustomEnum')

Make an `Enum` whose member names are `str(value)` for each value of `iterable`.

```pycon
>>> E = iterable_to_enum([1, 'two'])
>>> list(E)
[<CustomEnum.1: 1>, <CustomEnum.two: 'two'>]
>>> E['1'].value
1
```

### front.util.normalize_map(map)

Resolve a `Map` (mapping, callable returning one, or None) to a mapping; None gives `{}`.

* **Return type:**
  [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)

```pycon
>>> normalize_map(None), normalize_map({'a': 1}), normalize_map(lambda: {'b': 2})
({}, {'a': 1}, {'b': 2})
```

### front.util.obj_name(func)

Get the name of a callable, or make one (`UnnamedObjectNNN`) for lambdas and nameless objects.

### front.util.subdict(d, keys=None)

Get a sub-dict of Mapping `d`, with only those keys that are both in `keys` and `d`.

Note that the dict will be ordered as `keys` are, so can be used for reordering
a Mapping.

```pycon
>>> subdict({'a': 1, 'b': 2, 'c': 3, 'd': 4}, keys=['b', 'a', 'd'])
{'b': 2, 'a': 1, 'd': 4}
```
