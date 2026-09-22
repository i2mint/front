# front.elements.implementation

Helpers for binding concrete UI component factories to front element classes.

`implement_component` is a small factory that produces a `render`-able
front element class from any callable component factory (e.g. a Streamlit
widget), wiring the factory’s keyword arguments to the element’s attributes.

### Functions

| [`implement_component`](#front.elements.implementation.implement_component)(base_cls, component_factory)   | Make a `base_cls` subclass whose `render` calls `component_factory` with the element's attributes.   |
|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|

### front.elements.implementation.implement_component(base_cls, component_factory, input_value_callback=None, \*\*input_mapping)

Make a `base_cls` subclass whose `render` calls `component_factory` with the element’s attributes.

For each keyword-able parameter of `component_factory`, the element attribute
of the same name (or of the name given in `input_mapping`) is passed, unless
it is None; callable attributes are called first. The value returned by the
factory is handed to `input_value_callback(value, element)` if given, and
returned.

```pycon
>>> from dataclasses import dataclass
>>> from front.elements import FrontComponentBase
>>> def widget(label, value=0):
...     return f"{label}={value}"
>>> @dataclass
... class LabelBase(FrontComponentBase):
...     label: str = None
...     value: int = 0
>>> Component = implement_component(LabelBase, widget)
>>> Component(label='n', value=7)()
'n=7'
```

With `input_mapping`, the factory’s `label` is fed from the element’s `name`:

```pycon
>>> seen = []
>>> Component = implement_component(
...     LabelBase, widget, input_value_callback=lambda v, el: seen.append(v), label='name'
... )
>>> Component(name='count', value=2)()
'count=2'
>>> seen
['count=2']
```
