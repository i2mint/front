# front.dag

Crudify the variable nodes of a `meshed` DAG.

Crudifying a var node of a DAG means: the function producing it stores its
output in a store and returns the key, and the functions consuming it take that
key and fetch the value from the same store. The stores live in a mall (a
mapping of store names to stores).

Main entry points:

- `crudify_func_nodes`: a copy of the DAG whose func nodes are crudified.
- `crudify_funcs`: just the (crudified) functions of those func nodes.

See below one of the dags that will often be used in this module’s doctests:

```pycon
>>> from meshed.makers import code_to_dag
>>> @code_to_dag
... def dag():
...     x = foo(a, b)
...     y = bar(x, greeting)
...     z = confuser(a, w=x)  # note the w=x to test non-trivial binding
>>> print(dag.dot_digraph_ascii())
```

```text
   ┌──────────┐
┌▶ │ confuser │ ◀──    a
│  └──────────┘
│    │                │
│    │                │
│    ▼                ▼
│                   ┌─────┐
│       z           │ foo │ ◀──  b
│                   └─────┘
│                     │
│                     │
│                     ▼
│
└──────────────────    x

                      │
                      │
                      ▼
                    ┌─────┐
     greeting   ──▶ │ bar │
                    └─────┘
                      │
                      │
                      ▼

                       y
```

### Functions

| [`crudify_func_nodes`](#front.dag.crudify_func_nodes)(var_nodes, dag[, ...])   | Crudifies the given `var_nodes` in the `dag`.                                             |
|----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| [`crudify_funcs`](#front.dag.crudify_funcs)(var_nodes, dag[, ...])        | Like `crudify_func_nodes`, but return the list of (crudified) functions, not a DAG.       |
| [`fnodes_to_var_node_crude_specs`](#front.dag.fnodes_to_var_node_crude_specs)(fnodes)      | Yield `(var, func, bind)` triples of the given func nodes.                                |
| [`group_kvs_into_dict`](#front.dag.group_kvs_into_dict)(kvs)                    | Group `(key, value)` pairs into a `{key: [values]}` dict, keeping order.                  |
| [`simple_namer`](#front.dag.simple_namer)(name, \*[, prefix, suffix])    | Wrap `name` with a `prefix` and `suffix`; the default store namer uses `suffix='_store'`. |

### Classes

| [`VarNodeRole`](#front.dag.VarNodeRole)(\*values)   | (Var)Node roles.   |
|--------------------------------------------------------------------------|--------------------|

### *class* front.dag.VarNodeRole(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

(Var)Node roles.

When a `VarNode` is used to source the arguments of a `FuncNode`, it’s playing
a `VarNodeRole.argument` role.

When a `VarNode` is used to store the return value of a `FuncNode`, it’s playing
a `VarNodeRole.return_value` role.

Most `VarNode``s play both roles during a ``DAG` computation.

### front.dag.crudify_func_nodes(var_nodes, dag, var_node_name_to_store_name=functools.partial(<function simple_namer>, suffix='_store'), \*, mall=None, include_stores_attribute=False, save_name_param='save_name')

Crudifies the given `var_nodes` in the `dag`.

Crudifying a var node means crudifying it’s `FuncNode` neighbors,
i.e. telling the function that outputs to the `VarNode` (if any) to save it’s
output in a store and (additionally) return the key it saved it too instead of the
value itself, and telling any consumers of the var node to use that key as it’s
argument instead, retrieving the value from said store.

```pycon
>>> from meshed import DAG, FuncNode
>>> from inspect import signature
>>> def foo(a, b):  return a + b
>>> def bar(x, y):  return  x * y
>>> dag = DAG([
...     FuncNode(foo, name='foo', out='foo_output'),
...     FuncNode(bar, bind={'y': 'foo_output'})
... ])
```

Let’s crudify `'foo_output'`. We don’t need to specify a mall, since
`crudify_func_nodes` will make one for us.
But in order to get access to it, to see what the function is doing, let’s define
a mall with a single store (a dictionary), named `'foo_output_store'`
(note that the map between `var_node` string name and
store name is controlled by the `var_node_name_to_store_name` argument)

```pycon
>>> store = dict()
>>> mall = {'foo_output_store': store}
>>> new_dag = crudify_func_nodes(['foo_output'], dag, mall=mall)
```

The `new_dag` will have the same global behavior:

```pycon
>>> assert dag(2, 3, 4) == new_dag(2, 3, 4) == 20
```

Notice though, that the `foo` node will have an extra argument, `save_name`,
which is the name of the store to save the output to:

```pycon
>>> print(new_dag.synopsis_string())
a,b,save_name -> foo -> foo_output
foo_output,x -> bar_ -> bar
```

This difference will be reflected in the signature of the `new_dag`:

```pycon
>>> print(str(signature(dag)))
(a, b, x)
>>> print(str(signature(new_dag)))
(a, b, x, save_name: str = '')
```

Let’s have a closer look at the functions that `dag` and `new_dag` are
using. The functions of the `dag` are the original functions we specified,
behaving normally:

```pycon
>>> dag.func_nodes[0].func(2, 3)
5
>>> dag.func_nodes[1].func(4, 5)
20
```

But the first function of `new_dag` outputs `'bar_last_output'` instead of `5`.

```pycon
>>> new_dag.func_nodes[0].func(2, 3)
'bar_last_output'
```

Where did the `5` go? In the mall!

```pycon
>>> mall
{'foo_output_store': {'bar_last_output': 5}}
```

So that `5` has been stored under the `'bar_last_output'` key.
Further, the second function’s second argument will no longer work with numbers,
but with string keys, and use that same store to retrieve the value it needs for
the underlying function:

```pycon
>>> new_dag.func_nodes[1].func(4, 'bar_last_output')
20
```

This `'bar_last_output'` was only the default value that is used if
`save_name` is not given. If we give it a different name, the value will be
stored under that name instead:

```pycon
>>> new_dag.func_nodes[0].func(20, 22, save_name='my_save_name')
'my_save_name'
>>> mall
{'foo_output_store': {'bar_last_output': 5, 'my_save_name': 42}}
```

* **Parameters:**
  * **var_nodes** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – The `VarNodes` we want to crudify
  * **dag** (`DAG`) – The dag that contains these var_nodes
  * **var_node_name_to_store_name** – The function to use to make a store for a given
    var_node name. If you have an explicit mapping `m` for this, just use `m.get`
  * **mall** ([`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]] | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – A `mall` (store of stores, i.e. mapping of mappings) whose keys are
    store names, and values are the actual stores.
  * **include_stores_attribute** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Whether the crudified functions should have an
    attribute containing a pointer to the stores involved
  * **save_name_param** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The name that the “save as” parameter should appear as.
* **Returns:**

### front.dag.crudify_funcs(var_nodes, dag, var_node_name_to_store_name=functools.partial(<function simple_namer>, suffix='_store'), \*, mall=None, include_stores_attribute=False, save_name_param='save_name')

Like `crudify_func_nodes`, but return the list of (crudified) functions, not a DAG.

See `crudify_func_nodes` for the meaning of the arguments.

### front.dag.fnodes_to_var_node_crude_specs(fnodes)

Yield `(var, func, bind)` triples of the given func nodes.

### front.dag.group_kvs_into_dict(kvs)

Group `(key, value)` pairs into a `{key: [values]}` dict, keeping order.

```pycon
>>> group_kvs_into_dict([('a', 1), ('b', 2), ('a', 3)])
{'a': [1, 3], 'b': [2]}
```

### front.dag.simple_namer(name, , prefix='', suffix='')

Wrap `name` with a `prefix` and `suffix`; the default store namer uses `suffix='_store'`.

```pycon
>>> simple_namer('x', suffix='_store')
'x_store'
```
