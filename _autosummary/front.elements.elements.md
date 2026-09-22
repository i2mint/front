# front.elements.elements

Abstract base classes for the composite tree of front UI elements.

Front elements (containers, inputs, outputs, etc.) are arranged in a tree
mirroring the rendering specification. This module defines the base
`FrontElementBase` and `FrontContainerBase` classes that concrete frontends
(e.g. streamlit) subclass to provide their own rendering.

### Functions

| [`mk_element_from_spec`](#front.elements.elements.mk_element_from_spec)(spec)          | Instantiate the element factory found under `ELEMENT_KEY` with the other keys.       |
|--------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| [`mk_input_element_specs`](#front.elements.elements.mk_input_element_specs)(obj, inputs) | Make one input element spec per parameter of `obj`, from a type-keyed `inputs` spec. |

### Classes

| [`BooleanInputBase`](#front.elements.elements.BooleanInputBase)([obj, name, display, ...])      | Boolean input (checkbox-like); values are cast with `bool`, defaulting to False.              |
|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| [`ExecContainerBase`](#front.elements.elements.ExecContainerBase)(obj, inputs, output[, ...])    | Container that executes `obj` with the values of its input children.                          |
| [`FileUploaderBase`](#front.elements.elements.FileUploaderBase)([obj, name, display, ...])      | File upload input, restricted to the given file `type` (extension(s)) if any.                 |
| [`FloatInputBase`](#front.elements.elements.FloatInputBase)([obj, name, display, ...])        | Float input with optional bounds and `step`; values are cast with `float`, defaulting to 0.0. |
| [`FrontComponentBase`](#front.elements.elements.FrontComponentBase)([obj, name, display])         | A leaf element the user interacts with (an input, an output, a text section).                 |
| [`FrontContainerBase`](#front.elements.elements.FrontContainerBase)([obj, name, display])         | An element with children, each built from a keyword argument holding an element spec.         |
| [`FrontElementBase`](#front.elements.elements.FrontElementBase)([obj, name, display])           | Base of every front element: a renderable node of the element tree.                           |
| [`FrontElementSpec`](#front.elements.elements.FrontElementSpec)                                 |                                                                                               |
| [`InputBase`](#front.elements.elements.InputBase)([obj, name, display, input_key, ...])  | Base of input components: a value bound to state under `input_key`.                           |
| [`IntInputBase`](#front.elements.elements.IntInputBase)([obj, name, display, ...])          | Integer input with optional bounds; values are cast with `int`, defaulting to 0.              |
| [`KwargsInputBase`](#front.elements.elements.KwargsInputBase)([obj, name, display, ...])       | Input for a `**kwargs` parameter, with one sub-input per name in `func_sig`.                  |
| [`MultiSourceInputBase`](#front.elements.elements.MultiSourceInputBase)([obj, name, display, ...])  | An input whose value can come from several child input components.                            |
| [`NumberInputBase`](#front.elements.elements.NumberInputBase)([obj, name, display, ...])       | Base of numeric inputs, with an optional display `format`.                                    |
| [`OutputBase`](#front.elements.elements.OutputBase)([obj, name, display])                 | Base of output components; `output` is set by the executing container before render.          |
| [`SelectorBase`](#front.elements.elements.SelectorBase)([obj, name, display, ...])          | Input choosing one value among `options` (a sequence, or a callable returning one).           |
| [`TextInputBase`](#front.elements.elements.TextInputBase)([obj, name, display, ...])         | Text input; the view value defaults to the empty string.                                      |
| [`TextSectionBase`](#front.elements.elements.TextSectionBase)(content[, kind, obj, name, ...]) | A component displaying text `content` of a given `kind` (e.g. "text", "markdown").            |

### *class* front.elements.elements.BooleanInputBase(obj=None, name=None, display=True, input_key=None, value=ValueNotSet, on_value_change=None, bound_data_factory=None, is_noneable=False, disabled=False)

Bases: [`InputBase`](#front.elements.elements.InputBase)

Boolean input (checkbox-like); values are cast with `bool`, defaulting to False.

### *class* front.elements.elements.ExecContainerBase(obj, inputs, output, name=None, display=True, auto_submit=False, on_submit=None)

Bases: [`FrontContainerBase`](#front.elements.elements.FrontContainerBase)

Container that executes `obj` with the values of its input children.

Builds one input child per parameter of `obj` (see `mk_input_element_specs`)
plus an `output` child. `_submit` calls `obj` with the collected inputs,
hands the result to the first `OutputBase` child and renders it, then calls
`on_submit` with the result if given. Concrete subclasses implement `render`
and `_noneable` (how an optional input is presented).

### *class* front.elements.elements.FileUploaderBase(obj=None, name=None, display=True, input_key=None, value=ValueNotSet, on_value_change=None, bound_data_factory=None, is_noneable=False, disabled=False, type=None, accept_multiple_files=False)

Bases: [`InputBase`](#front.elements.elements.InputBase)

File upload input, restricted to the given file `type` (extension(s)) if any.

### *class* front.elements.elements.FloatInputBase(obj=None, name=None, display=True, input_key=None, value=ValueNotSet, on_value_change=None, bound_data_factory=None, is_noneable=False, disabled=False, format=None, min_value=None, max_value=None, step=None)

Bases: [`NumberInputBase`](#front.elements.elements.NumberInputBase)

Float input with optional bounds and `step`; values are cast with `float`, defaulting to 0.0.

### *class* front.elements.elements.FrontComponentBase(obj=None, name=None, display=True)

Bases: [`FrontElementBase`](#front.elements.elements.FrontElementBase)

A leaf element the user interacts with (an input, an output, a text section).

### *class* front.elements.elements.FrontContainerBase(obj=None, name=None, display=True, \*\*kwargs)

Bases: [`FrontElementBase`](#front.elements.elements.FrontElementBase)

An element with children, each built from a keyword argument holding an element spec.

Every extra keyword argument is a child spec: the key becomes the child’s
`name` (unless the spec overrides it) and the container’s `obj` is passed
down. Concrete containers define the layout in `render`.

```pycon
>>> from dataclasses import dataclass
>>> @dataclass
... class Hello(FrontElementBase):
...     def render(self):
...         return f"hello {self.name}"
>>> class Box(FrontContainerBase):
...     def render(self):
...         return [child() for child in self.children]
>>> box = Box(name='box', greeting={ELEMENT_KEY: Hello, 'name': 'you'}, other={ELEMENT_KEY: Hello})
>>> box()
['hello you', 'hello other']
```

### *class* front.elements.elements.FrontElementBase(obj=None, name=None, display=True)

Bases: [`ABC`](https://docs.python.org/3/library/abc.html#abc.ABC)

Base of every front element: a renderable node of the element tree.

Subclasses implement `render`. Calling the element runs the lifecycle
`pre_render` → `render` → `post_render` when `display` is truthy, and
does nothing (returns None) otherwise. `name` and `display` may be given
as callables of `obj`; they are resolved at construction.

```pycon
>>> from dataclasses import dataclass
>>> @dataclass
... class Hello(FrontElementBase):
...     def render(self):
...         return f"hello {self.name}"
>>> Hello(name='world')()
'hello world'
>>> Hello(obj=len, name=lambda obj: obj.__name__)()
'hello len'
>>> Hello(name='hidden', display=False)() is None
True
```

#### SEE ALSO
`FrontContainerBase`: an element with children.
`FrontComponentBase`: a leaf element the user interacts with.

#### post_render(render_result)

Hook run on the result of `render`; returns it unchanged by default.

#### pre_render()

Hook run before `render`; does nothing by default.

#### *abstractmethod* render()

Render the element with the concrete UI framework; must be overridden.

### *class* front.elements.elements.FrontElementSpec

Bases: [`TypedDict`](https://docs.python.org/3/library/typing.html#typing.TypedDict)

### *class* front.elements.elements.InputBase(obj=None, name=None, display=True, input_key=None, value=ValueNotSet, on_value_change=None, bound_data_factory=None, is_noneable=False, disabled=False)

Bases: [`FrontComponentBase`](#front.elements.elements.FrontComponentBase)

Base of input components: a value bound to state under `input_key`.

`obj` is the `inspect.Parameter` the input feeds. At construction, `value`
is wrapped in a `BoundData` made by `bound_data_factory` (unless it already
is one), and seeded with the given value or the parameter’s default if nothing
is set yet. Two companion keys, `view_key` and `none_key`, hold the widget’s
displayed value and its “is None” toggle.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – If `bound_data_factory` is None when a `BoundData` is needed.

#### *property* none_key *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

`"{input_key}_none"`.

* **Type:**
  State key of the “value is None” toggle

#### on_change()

Call `on_value_change` with the current view value, if both are set.

#### post_render(render_result)

Store the rendered (widget) value in the bound state and return it.

#### *property* view_key *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

`"{input_key}_view"`.

* **Type:**
  State key of the widget’s displayed value

### *class* front.elements.elements.IntInputBase(obj=None, name=None, display=True, input_key=None, value=ValueNotSet, on_value_change=None, bound_data_factory=None, is_noneable=False, disabled=False, format=None, min_value=None, max_value=None)

Bases: [`NumberInputBase`](#front.elements.elements.NumberInputBase)

Integer input with optional bounds; values are cast with `int`, defaulting to 0.

### *class* front.elements.elements.KwargsInputBase(obj=None, name=None, display=True, input_key=None, value=ValueNotSet, on_value_change=None, bound_data_factory=None, is_noneable=False, disabled=False, inputs=None, func_sig=None)

Bases: [`InputBase`](#front.elements.elements.InputBase)

Input for a `**kwargs` parameter, with one sub-input per name in `func_sig`.

#### pre_render()

Make `self.get_kwargs`, a function with signature `func_sig` returning its kwargs.

### *class* front.elements.elements.MultiSourceInputBase(obj=None, name=None, display=True, input_key=None, value=ValueNotSet, on_value_change=None, bound_data_factory=None, is_noneable=False, disabled=False, \*\*kwargs)

Bases: [`InputBase`](#front.elements.elements.InputBase)

An input whose value can come from several child input components.

Extra keyword arguments are child input specs; each child shares this input’s
`input_key`, `value` and binding settings.

### *class* front.elements.elements.NumberInputBase(obj=None, name=None, display=True, input_key=None, value=ValueNotSet, on_value_change=None, bound_data_factory=None, is_noneable=False, disabled=False, format=None)

Bases: [`InputBase`](#front.elements.elements.InputBase)

Base of numeric inputs, with an optional display `format`.

### *class* front.elements.elements.OutputBase(obj=None, name=None, display=True)

Bases: [`FrontComponentBase`](#front.elements.elements.FrontComponentBase)

Base of output components; `output` is set by the executing container before render.

### *class* front.elements.elements.SelectorBase(obj=None, name=None, display=True, input_key=None, value=ValueNotSet, on_value_change=None, bound_data_factory=None, is_noneable=False, disabled=False, options=None)

Bases: [`InputBase`](#front.elements.elements.InputBase)

Input choosing one value among `options` (a sequence, or a callable returning one).

If no options are given and the parameter is annotated with a `Literal`, the
literal’s values are the options.

#### pre_render()

Resolve the options and pre-select the current view value (or the first option).

### *class* front.elements.elements.TextInputBase(obj=None, name=None, display=True, input_key=None, value=ValueNotSet, on_value_change=None, bound_data_factory=None, is_noneable=False, disabled=False, type=None)

Bases: [`InputBase`](#front.elements.elements.InputBase)

Text input; the view value defaults to the empty string.

### *class* front.elements.elements.TextSectionBase(content, kind='text', obj=None, name=None, display=True, \*\*kwargs)

Bases: [`FrontComponentBase`](#front.elements.elements.FrontComponentBase)

A component displaying text `content` of a given `kind` (e.g. “text”, “markdown”).

`content` and `kind` may be callables of `obj`, resolved at construction.
Extra keyword arguments are kept in `self.kwargs` for the concrete renderer.

### front.elements.elements.mk_element_from_spec(spec)

Instantiate the element factory found under `ELEMENT_KEY` with the other keys.

```pycon
>>> from dataclasses import dataclass
>>> @dataclass
... class Hello(FrontElementBase):
...     def render(self):
...         return f"hello {self.name}"
>>> mk_element_from_spec({ELEMENT_KEY: Hello, 'name': 'x'})()
'hello x'
```

* **Raises:**
  [**RuntimeError**](https://docs.python.org/3/builtins/exceptions.html#RuntimeError) – If `spec` has no `ELEMENT_KEY`.

### front.elements.elements.mk_input_element_specs(obj, inputs)

Make one input element spec per parameter of `obj`, from a type-keyed `inputs` spec.

`inputs` maps parameter types (and/or parameter names) to element specs; the
`DEFAULT_INPUT_KEY` entry is merged under every type entry. Each parameter’s
spec is looked up by its annotation (or the type of its default), with an
`Optional[X]` annotation or a `None` default marking it as `is_noneable`.
Unions of more than one non-None type are not supported.

```pycon
>>> def foo(a: int, b='hi', c: float = None):
...     pass
>>> specs = mk_input_element_specs(
...     foo, {DEFAULT_INPUT_KEY: {'disabled': False}, int: {'min_value': 0}}
... )
>>> list(specs)
['a', 'b', 'c']
>>> {k: v for k, v in specs['a'].items() if k != 'obj'}
{'disabled': False, 'min_value': 0, 'input_key': 'foo_a', 'is_noneable': False}
>>> specs['c']['is_noneable']
True
```

* **Raises:**
  [**NotImplementedError**](https://docs.python.org/3/builtins/exceptions.html#NotImplementedError) – If a parameter is annotated with a Union of several
  non-None types.
