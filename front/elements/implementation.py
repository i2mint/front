"""Helpers for binding concrete UI component factories to front element classes.

``implement_component`` is a small factory that produces a ``render``-able
front element class from any callable component factory (e.g. a Streamlit
widget), wiring the factory's keyword arguments to the element's attributes.
"""

from collections.abc import Callable
from i2 import Sig


def implement_component(
    base_cls: type,
    component_factory: Callable,
    input_value_callback: Callable = None,
    **input_mapping,
):
    """Make a ``base_cls`` subclass whose ``render`` calls ``component_factory`` with the element's attributes.

    For each keyword-able parameter of ``component_factory``, the element attribute
    of the same name (or of the name given in ``input_mapping``) is passed, unless
    it is None; callable attributes are called first. The value returned by the
    factory is handed to ``input_value_callback(value, element)`` if given, and
    returned.

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

    With ``input_mapping``, the factory's ``label`` is fed from the element's ``name``:

    >>> seen = []
    >>> Component = implement_component(
    ...     LabelBase, widget, input_value_callback=lambda v, el: seen.append(v), label='name'
    ... )
    >>> Component(name='count', value=2)()
    'count=2'
    >>> seen
    ['count=2']
    """
    component_factory_sig = Sig(component_factory)
    keyword_names = component_factory_sig.keyword_names

    class component_class(base_cls):
        def render(self):
            component_factory_kwargs = {}
            for name in keyword_names:
                attr_name = input_mapping.get(name, name)
                attr = getattr(self, attr_name, None)
                if attr is not None:
                    attr = attr() if callable(attr) else attr
                    component_factory_kwargs[name] = attr
            input_value = component_factory(**component_factory_kwargs)
            if input_value_callback:
                input_value_callback(input_value, self)
            return input_value

    return component_class
