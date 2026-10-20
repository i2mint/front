# front.tooltips

Tooltips for functions and their arguments.

Backend-agnostic helpers that compute tooltip text, to be attached to the specs/elements
a UI framework renders.

Function tooltips are a function of the docs (`func_tooltip`): the first non-blank
line, the first few lines, or everything before the first doctest – or an explicit string.

Argument tooltips (`param_tooltips`) are parsed from the docs (numpy, google and rest
styles are tried), overridden by a ledger (mapping) of explicit tooltips; and the params
can be selected with `include` / `exclude`.

```pycon
>>> def foo(a, b=2):
...     '''Add things.
...
...     More details here.
...
...     :param a: the first thing
...     :param b: the second thing
...
...     >>> foo(1)
...     3
...     '''
>>> func_tooltip(foo)
'Add things.'
>>> func_tooltip(foo, style='before_doctest')
'Add things.\n\nMore details here.\n\n:param a: the first thing\n:param b: the second thing'
>>> func_tooltip(foo, style='Explicit text')
'Explicit text'
>>> param_tooltips(foo)
{'a': 'the first thing', 'b': 'the second thing'}
>>> param_tooltips(foo, exclude=['b'], ledger={'a': 'override'})
{'a': 'override'}
```

### Functions

| [`apply_tooltips`](#front.tooltips.apply_tooltips)(obj_spec, obj)                    | Return `obj_spec` with `tooltip` entries computed for `obj` and its params.   |
|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`func_tooltip`](#front.tooltips.func_tooltip)(func[, style, n_lines, ellipsis])   | Tooltip for a function.                                                       |
| [`param_tooltips`](#front.tooltips.param_tooltips)(func, \*[, ledger, include, ...]) | Tooltips for the arguments of a function, as a `{param_name: tooltip}` dict.  |

### front.tooltips.apply_tooltips(obj_spec, obj)

Return `obj_spec` with `tooltip` entries computed for `obj` and its params.

The (opt-in) configuration is the `"tooltips"` entry of the spec, which is consumed
here and never reaches the elements. Being part of the rendering spec, it can sit under
a type (`Callable`) to apply to everything, or under an object’s name to apply to it
alone:

```default
{'tooltips': True}                       # all defaults
{'tooltips': {'func': 'first_lines',     # or any other string: explicit tooltip
              'params': {'exclude': ['x'], 'ledger': {'a': 'explicit'}}}}
{'tooltips': {'func': False}}            # no function tooltip, params only
```

The function tooltip goes to the spec’s `tooltip` and the param tooltips to
`execution.inputs.<param>.tooltip` (only for a spec that has an `execution` entry).
A `tooltip` the spec already has is kept.

Opt-in also means the element factories must accept `tooltip`: `FrontElementBase`
and the base containers do, but a concrete element with its own `__init__` signature
has to take it (and forward it) before the config is switched on for it.

```pycon
>>> def foo(a, b=2):
...     '''Add things.
...
...     :param a: the first thing
...     '''
>>> spec = apply_tooltips({'tooltips': True, 'execution': {'inputs': {}}}, foo)
>>> spec['tooltip'], spec['execution']['inputs']
('Add things.', {'a': {'tooltip': 'the first thing'}})
>>> apply_tooltips({'x': 1}, foo)
{'x': 1}
```

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### front.tooltips.func_tooltip(func, style='first_line', , n_lines=3, ellipsis='... (+more)')

Tooltip for a function.

* **Parameters:**
  **style** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – One of `'first_line'` (first non-blank line, stripped),
  `'first_lines'` (first `n_lines` non-blank lines, with `ellipsis` if cut),
  `'before_doctest'` (everything before the first doctest), or any other string,
  which is taken as the explicit tooltip.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### front.tooltips.param_tooltips(func, , ledger=None, include=None, exclude=(), doc_styles=('numpy', 'google', 'rest'))

Tooltips for the arguments of a function, as a `{param_name: tooltip}` dict.

Parsed from the docstring (first style in `doc_styles` that yields something),
then overridden by `ledger` (explicit tooltips). `include` (“only these”)
and `exclude` (“all except”) restrict the names.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
