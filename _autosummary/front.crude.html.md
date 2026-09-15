# front.crude

Crudify functions: let complex arguments be specified by string keys into stores.

CRUDE stands for CRUD-Execution.
It is a method to solve the problem of dealing with complex python objects in an
environment that doesn’t natively support these.

The method’s trick is to allow the complex object’s that we “crudified” to be controlled
via a string key that references the complex object, via a “store” which maps
these string keys to the actual physical object.
This store could be a python dictionary (so in RAM) or any persisting storage system
(files, DB) that is given a `typing.Mapping` interface
(see [https://i2mint.github.io/dol/](https://i2mint.github.io/dol/) or [https://i2mint.github.io/py2store](https://i2mint.github.io/py2store) for
tools to do so).

Take, for instance, a GUI that allows a user to compute some descriptive statistics
of the columns of a table.
The inputs are a table, and one of the following statistics function:
`statistics.mean`, `statistics.median`, or `statistics.stdev`.

Python functions are not a type natively handled by GUI, so what can we do?
We can stick a layer between our `compute_stats(stats_func, table)` function
and our GUI, endowed with a
`{"mean": statistics.mean`, “median”: statistics.median, “std”: statistics.stdev}\`\`
mapping. We expose the string keys to the GUI, and map them to the functions before
calling `compute_stats`.

In the case of the `table`, we’d probably add a means for the GUI user to upload
tables (say from `.csv` or `.xlsx` files), storing them under a name of their
choice, then pointing to said table via the name, when they want to execute a
`compute_stats(stats_func, table)`.

These are examples of what we call “crudifying” variables or functions.

Here we therefore offer tools to do this sort of thing;
wrap functions so that the complex arguments can be specified through a string key
that points to the actual python object (which is stored in a session’s memory or
persisted in some fashion).

### Functions

| [`auto_key`](#front.crude.auto_key)(\*args, \*\*kwargs)                     | Make a str key from arguments.                                                                        |
|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| [`auto_key_from_arguments`](#front.crude.auto_key_from_arguments)(\*args, \*\*kwargs)      | Make a str key from arguments.                                                                        |
| [`auto_key_from_time`](#front.crude.auto_key_from_time)(\*args[, \_\_format])         | Make a str key with current timestamp (ignoring arguments).                                           |
| [`crudify_based_on_names`](#front.crude.crudify_based_on_names)(func, \*[, ...])          | Crudify `func` from general, name-keyed `param_to_mall_map` and `output_store` specs.                 |
| [`keys_to_values_if_non_mapping_iterable`](#front.crude.keys_to_values_if_non_mapping_iterable)(d)        | Turn a non-mapping iterable into an identity dict; pass mappings through; None gives `{}`.            |
| [`mk_mall_of_dill_stores`](#front.crude.mk_mall_of_dill_stores)([store_names, rootdir])   | Make a mall of `DillFiles` stores, one sub-directory of `rootdir` per store name.                     |
| `prepare_for_crude_dispatch`([func, ...])                                                         | Wrap `func` into something that is ready for CRUDE dispatch.                                          |
| [`simple_mall_dispatch_core_func`](#front.crude.simple_mall_dispatch_core_func)(key, action, ...) | Explore a mall from a UI: list its stores, list a store's keys, or get a value.                       |
| `store_on_output`([func, store, ...])                                                             | Wrap `func` with an extra `save_name_param` argument that saves the output under that key in a store. |

### Classes

| [`Crudifier`](#front.crude.Crudifier)([param_to_mall_map, mall, ...])   | Convenience class to make crudify (i.e. map/source inputs of) functions.                 |
|----------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| [`DillFiles`](#front.crude.DillFiles)(\*args[, delete_func])            | Local files store that serializes values with dill (or pickle if dill is not installed). |

### *class* front.crude.Crudifier(param_to_mall_map=None, mall=None, include_stores_attribute=False, output_store=None, store_multi_values=False, save_name_param='save_name', empty_name_callback=None, auto_namer=None, output_trans=None, verbose=True)

Bases: `_Crudifier`

Convenience class to make crudify (i.e. map/source inputs of) functions.

See [https://github.com/i2mint/front/issues/21](https://github.com/i2mint/front/issues/21).

`prepare_for_crude_dispatch` works well if you want to crudify a single function,
but if you’re trying to crudify multiple functions according to a specific fixed
convention, using it directly would involve too much boilerplate.

`Crudifier` is one the tools we offer to reduce this boilerplate.

Here are a few examples of how to use it.

```pycon
>>> def foo(x, y):
...     return x + y
...
>>> def bar(a, x):
...     return a * x
```

Let’s say we want `x` to be sourced by the `x_store` mapping listed in the
`mall`. We can make a `crudify` function like this:

```pycon
>>> crudify = Crudifier(
...     param_to_mall_map={'x': 'x_store'}, mall={'x_store': {'stored_two': 2, 'stored_four': 4}}
... )
```

And apply it to any function containing a argumennt named `x`:

```pycon
>>> from inspect import signature
>>> crudified_foo = crudify(foo)
>>> str(signature(crudified_foo))  # note how x has now a Literal annotation showing what the valid str inputs are
"(x: Literal['stored_two', 'stored_four'], y)"
>>> crudified_foo('stored_two', 3)  # -> 2 + 3
5
>>> crudified_bar = crudify(bar)
>>> str(signature(crudified_bar))
"(a, x: Literal['stored_two', 'stored_four'])"
>>> crudified_bar(3, 'stored_two')  # -> 3 * 2
6
```

If the argument names correspond to `mall` key, the first `param_to_mall_map`
argument can be specified a list of arguments, or even a space-separated string of
these argument names. In the following, the `'x y'` is equivalent to
`['x', 'y']`, which is equivalent to `{'x': 'x', 'y', 'y'}`.

```pycon
>>> crudify = Crudifier('x y', mall={'x': {'stored_two': 2, 'stored_four': 4}, 'y': {'three': 3}})
>>> f = crudify(foo)
>>> str(signature(f))  # note that both x and y have a str annotation now
"(x: Literal['stored_two', 'stored_four'], y: Literal['three'])"
>>> f('stored_two', 'three')
5
```

This allows you to do things like partialize, to fix the mall, and only have to
specify the param_to_mall_map when you want to crudify.
In the following, note the `verbose=False` which tells the crudification not to
issue any warning when it sees we have keys in our `mall` that are not arguments
of the function.

```pycon
>>> from functools import partial
>>>
>>> mall = {
...     'x': {'stored_two': 2}, 'y': {'three': 3}, 'fall_back_store': {'zebra': 11}
... }
>>> Crudify = partial(Crudifier, mall=mall, verbose=False)
>>> f = Crudify('x')(foo)
>>> f('stored_two', 3)
5
>>> f = Crudify('x y')(foo)
>>> f('stored_two', 'three')
5
>>> b = Crudify({'a': 'fall_back_store'})(bar)
>>> b('zebra', 3)
33
```

This callable object, or something like it, can then be used in a recursive
transformer such a the front rendering process to indicate that a function should
be crudified, and how.

For example, say we had a mini-language where this

```pycon
>>> config = {
...     foo: {
...         'preprocesses': Crudify('x y'),
...         'whatevs': 42
...     },
...     bar: {
...         'blahblah': 24
...     }
... }
```

should be preprocessed in such a way that adds a `'func'` key to each item of
`config` which contains a transformed function if a `preprocesses` function
or list of functions is specified, or the original function itself otherwise.
The following would implement this:

```pycon
>>> from typing import Iterable
>>> from i2 import Pipe
>>>
>>> def _ensure_iterable(v):
...     if not isinstance(v, Iterable):
...         v = [v]
...     return v
...
>>> def prepare(config):
...     for func, specs in config.items():
...         if (processes := specs.get('preprocesses', None)) is not None:
...             preprocess = Pipe(*_ensure_iterable(processes))
...             _func = preprocess(func)
...         else:
...             _func = func
...         specs = dict(specs, func=_func)
...         yield func, specs
```

```pycon
>>> prepared_configs = dict(prepare(config))
```

Now get the `func` value under `foo`, and see that it has been crudified:

```pycon
>>> processed_foo = prepared_configs[foo]['func']
>>> processed_foo('stored_two', 'three')
5
```

### *class* front.crude.DillFiles(\*args, delete_func=None, \*\*kwargs)

Bases: `Store`

Local files store that serializes values with dill (or pickle if dill is not installed).

#### is_valid_key(k, \*args, \_\_name='is_valid_key', \*\*kwargs)

`is_valid_key` on the inner key – see `mk_relative_path_store`.

#### validate_key(k, \*args, \_\_name='validate_key', \*\*kwargs)

`validate_key` on the inner key – see `mk_relative_path_store`.

### front.crude.auto_key(\*args, \*\*kwargs)

Make a str key from arguments.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> auto_key_from_arguments(1,2,c=3,d=4)
'1,2,c=3,d=4'
>>> auto_key_from_arguments(1,2)
'1,2'
>>> auto_key_from_arguments(c=3,d=4)
'c=3,d=4'
>>> auto_key_from_arguments()
''
```

### front.crude.auto_key_from_arguments(\*args, \*\*kwargs)

Make a str key from arguments.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> auto_key_from_arguments(1,2,c=3,d=4)
'1,2,c=3,d=4'
>>> auto_key_from_arguments(1,2)
'1,2'
>>> auto_key_from_arguments(c=3,d=4)
'c=3,d=4'
>>> auto_key_from_arguments()
''
```

### front.crude.auto_key_from_time(\*args, \_\_format=1000000.0, \*\*kwargs)

Make a str key with current timestamp (ignoring arguments).

* **Parameters:**
  **\_\_format** ([`Number`](https://docs.python.org/3/library/numbers.html#numbers.Number) | [`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)) – When a number, will be used as a multiplier of current utc time
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> auto_key_from_time()
'1_669_724_787_630_906'
```

But `auto_key_from_time` is really meant to be used with `functools.partial` to
parametrize its `__format`, such as:

```pycon
>>> from functools import partial
>>>
>>> time_in_ms = partial(auto_key_from_time, __format=1e3)
>>> normal_format = partial(auto_key_from_time, __format='%Y-%m-%d %H:%M:%S')
>>> modulo_1000 = partial(auto_key_from_time, __format=lambda x: int(x % 1000))
>>>
>>> time_in_ms()
'1_669_724_787_641'
>>> normal_format()
'2022-11-29 12:26:27'
>>> modulo_1000()
'788'
```

### front.crude.crudify_based_on_names(func, \*, param_to_mall_map=(), output_store=(), crudifier=<class 'front.crude.Crudifier'>)

Crudify `func` from general, name-keyed `param_to_mall_map` and `output_store` specs.

Meant to apply one crudification convention to many functions: the specs are
looked up per argument by `(func, arg_name)`, `(func_name, arg_name)`,
`"func_name.arg_name"` then `arg_name` (first match wins), and the output
store by `func` then `func_name`.

* **Parameters:**
  * **func** – The function to crudify.
  * **param_to_mall_map** – Mapping from those argument keys to mall keys.
  * **output_store** – Mapping from `func` or its name to an output store.
  * **crudifier** – The callable doing the crudification, given
    `(func, param_to_mall_map=..., output_store=...)`.
* **Returns:**
  The crudified function, or `func` itself if no spec matched.

```pycon
>>> from functools import partial
>>> def foo(x, y):
...     return x + y
>>> def bar(a, x):
...     return a * x
>>> general_crudifier = partial(
...     crudify_based_on_names,
...     param_to_mall_map={'x': 'x_store'},
...     crudifier=partial(prepare_for_crude_dispatch, mall={'x_store': {'stored_two': 2, 'stored_four': 4}})
... )
>>>
>>> foo, bar = map(general_crudifier, [foo, bar])
>>>
>>> foo('stored_two', 10)
12
>>> bar(4, 'stored_four')
16
```

### front.crude.keys_to_values_if_non_mapping_iterable(d)

Turn a non-mapping iterable into an identity dict; pass mappings through; None gives `{}`.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

```pycon
>>> keys_to_values_if_non_mapping_iterable(['a', 'b'])
{'a': 'a', 'b': 'b'}
>>> keys_to_values_if_non_mapping_iterable({'a': 's'})
{'a': 's'}
>>> keys_to_values_if_non_mapping_iterable(None)
{}
```

### front.crude.mk_mall_of_dill_stores(store_names=collections.abc.Iterable[str], rootdir=None)

Make a mall of `DillFiles` stores, one sub-directory of `rootdir` per store name.

`store_names` can be a space-separated string. `rootdir` defaults to a
stable `"crude"` subdirectory of the system temp directory (the same path
on every call, not a fresh one).

### front.crude.simple_mall_dispatch_core_func(key, action, store_name, mall)

Explore a mall from a UI: list its stores, list a store’s keys, or get a value.

This function is only meant to be a helper to give a UI (GUI,
CLI…) mall-exploration capabilities. Namely:

- `list(mall)`: list the keys of a mall. This is achieved with args:
  `(key=None, action=None, store_name=None, mall=mall)`
- `mall[store_name]`: get a store. Achieved by:
  `(key=None, action=None, store_name=store_name, mall=mall)`
- `list(mall[store_name])`: list keys of a store (of the mall). Achieved by:
  `(key=None, action='list', store_name=store_name, mall=mall)`
- `list(filter(key, mall[store_name]))`: list keys of a store (of the mall)
  according to a substring filter. (only keys that have `key` as substring)
  `(key=key, action='list', store_name=store_name, mall=mall)`
- `mall[store_name][key]`:  get the value/data of a store for `key`
  `(key=key, action='get', store_name=store_name, mall=mall)`

* **Parameters:**
  * **key** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The key
  * **action** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – ‘list’ (to list keys of a store) or ‘get’ (to get the value of
    `key` in the store (named `store_name`)
  * **store_name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Store name to look up in mall. If not given, the function will
    output the mall keys (which are valid store names)
  * **mall** ([`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]) – dict of stores (Mapping interface to data)
* **Returns:**

```pycon
>>> mall = {
...     'english': {'one': 1, 'two': 2, 'three': 3},
...     'french': {'un': 1, 'deux': 2},
... }
```

List the keys of a mall:

```pycon
>>> simple_mall_dispatch_core_func(None, None, None, mall=mall)
['english', 'french']
```

Get a store

```pycon
>>> simple_mall_dispatch_core_func(None, None, store_name='english', mall=mall)
{'one': 1, 'two': 2, 'three': 3}
```

List keys of a store (of the mall):

```pycon
>>> simple_mall_dispatch_core_func(
...     None, action='list', store_name='english', mall=mall
... )
['one', 'two', 'three']
```

List keys of a store (of the mall) according to a substring filter:

```pycon
>>> simple_mall_dispatch_core_func(
...     'e', action='list', store_name='english', mall=mall
... )
['one', 'three']
```

```pycon
>>> simple_mall_dispatch_core_func(
...     'two', action='get', store_name='english', mall=mall
... )
2
```
