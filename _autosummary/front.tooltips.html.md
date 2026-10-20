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

| [`func_tooltip`](#front.tooltips.func_tooltip)(func[, style, n_lines, ellipsis])   | Tooltip for a function.                                                      |
|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| [`param_tooltips`](#front.tooltips.param_tooltips)(func, \*[, ledger, include, ...]) | Tooltips for the arguments of a function, as a `{param_name: tooltip}` dict. |

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
