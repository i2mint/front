# front.py2pydantic

Bridge between plain Python functions and pydantic v2 models.

Given a Python function, produce a pydantic input model whose fields mirror
the function’s signature (names, annotations, defaults), and an “opyrator”-
style wrapper that takes a single pydantic model instance and dispatches
to the underlying function.

Useful for auto-generating forms, validators, and JSON-schema descriptions
of arbitrary callables — the core trick behind front’s app-from-function
dispatch.

```pycon
>>> from i2.tests.objects_for_testing import formula1
>>> pyd_input_model = func_to_pyd_input_model_cls(formula1)
>>> pyd_input_model.__name__
'formula1'
>>> from i2 import Sig
>>> Sig(formula1)
<Sig (w, /, x: float, y=1, *, z: int = 1)>
>>> Sig(pyd_input_model)
<Sig (*, w: Any, x: float, y: int = 1, z: int = 1) -> None>
```

```pycon
>>> pyd_func = func_to_pyd_func(formula1)
>>> input_model_instance = pyd_input_model(w=1, x=2)
>>> input_model_instance
formula1(w=1, x=2.0, y=1, z=1)
>>> pyd_func(input_model_instance)
3.0
>>> formula1(1, x=2)  # can't say w=1 because w is position only
3
```

### Functions

| [`func_to_pyd_func`](#front.py2pydantic.func_to_pyd_func)(func[, dflt_type])           | Get an 'opyrator' function from a python function: one taking a single pydantic model input.   |
|------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| [`func_to_pyd_input_model_cls`](#front.py2pydantic.func_to_pyd_input_model_cls)(func[, ...])      | Get a pydantic model of the arguments of a python function.                                    |
| [`func_to_pyd_model_specs`](#front.py2pydantic.func_to_pyd_model_specs)(func[, dflt_type])    | Helper function to get field info from python signature parameters.                            |
| [`pyd_func_ingress_template`](#front.py2pydantic.pyd_func_ingress_template)(...)                | Turn a pydantic model instance into the `(args, kwargs)` of `wrapped_func_sig`.                |
| [`pydantic_egress`](#front.py2pydantic.pydantic_egress)(output)                       | Wrap `output` in an `Output` model with a single `output_val` field of its type.               |
| [`pydantic_model_from_type`](#front.py2pydantic.pydantic_model_from_type)(mytype[, name, ...]) | Make a pydantic model with one required field `field_name` of type `mytype`.                   |

### front.py2pydantic.func_to_pyd_func(func, dflt_type=typing.Any)

Get an ‘opyrator’ function from a python function: one taking a single pydantic model input.

The output model is not yet applied: the wrapped function returns what `func` returns.

### front.py2pydantic.func_to_pyd_input_model_cls(func, dflt_type=typing.Any, , name=None, warn_when_changing_names=True)

Get a pydantic model of the arguments of a python function.

```pycon
>>> def foo(a, b: int, c: bool=False):
...     ...
>>> obj = func_to_pyd_input_model_cls(foo)
>>> obj.model_json_schema() == (
... {
...     'title': 'foo',
...     'type': 'object',
...     'properties': {
...         'a': {'title': 'A'},
...         'b': {'title': 'B', 'type': 'integer'},
...         'c': {'title': 'C', 'default': False, 'type': 'boolean'}
...     },
...     'required': ['a', 'b']
... })
True
```

If some argument names of the function conflict with attribute names of BaseModel,
these will be capitalized to resolve the conflict.

```pycon
>>> def bar(x, copy, schema):
...     ...
>>> obj2 = func_to_pyd_input_model_cls(bar, warn_when_changing_names=False)
>>> obj2.model_json_schema() == (
... {
...     'title': 'bar',
...     'type': 'object',
...     'properties': {
...         'x': {'title': 'X'},
...         'COPY': {'title': 'Copy'},
...         'SCHEMA': {'title': 'Schema'}},
...     'required': ['x', 'COPY', 'SCHEMA']
... })
True
```

### front.py2pydantic.func_to_pyd_model_specs(func, dflt_type=typing.Any)

Helper function to get field info from python signature parameters.

Each spec is a `(type, default)` tuple suitable for pydantic v2’s
`create_model`. For unannotated parameters the type is inferred from
the default value’s type when a default is present, otherwise
`dflt_type` (`Any` by default) is used with `...` (required).

### front.py2pydantic.pyd_func_ingress_template(input_model_instance, wrapped_func_sig)

Turn a pydantic model instance into the `(args, kwargs)` of `wrapped_func_sig`.

```pycon
>>> from i2 import Sig
>>> from i2.tests.objects_for_testing import formula1
>>> model = func_to_pyd_input_model_cls(formula1)(w=1, x=2)
>>> pyd_func_ingress_template(model, Sig(formula1))
((1,), {'x': 2.0, 'y': 1, 'z': 1})
```

### front.py2pydantic.pydantic_egress(output)

Wrap `output` in an `Output` model with a single `output_val` field of its type.

```pycon
>>> pydantic_egress(3)
Output(output_val=3)
```

### front.py2pydantic.pydantic_model_from_type(mytype, name='Output', field_name='result')

Make a pydantic model with one required field `field_name` of type `mytype`.

```pycon
>>> Model = pydantic_model_from_type(int)
>>> Model(result=2)
Output(result=2)
```
