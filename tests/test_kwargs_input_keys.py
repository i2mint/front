"""The nested inputs of a kwargs input are keyed by that input, not by ``get_kwargs``.

Regression test for i2mint/front#40: every parameter inside a ``KwargsInput`` used
to get the key ``get_kwargs_<param>``, so two kwargs inputs sharing a parameter name
shared their value, widget key and state.
"""

from dataclasses import dataclass
from inspect import Parameter

from i2 import Sig

from front.data_binding import BoundData
from front.elements.elements import KwargsInputBase, mk_input_element_specs


@dataclass
class _Kwargs(KwargsInputBase):
    def render(self):
        return None


def _nested_input_keys(input_key, state):
    kwargs_input = _Kwargs(
        obj=Parameter("kwargs", Parameter.VAR_KEYWORD),
        input_key=input_key,
        func_sig=Sig("data"),
        bound_data_factory=lambda k: BoundData(k, state),
    )
    kwargs_input.pre_render()
    specs = mk_input_element_specs(kwargs_input.get_kwargs, {})
    return {name: spec["input_key"] for name, spec in specs.items()}


def test_nested_input_keys_are_scoped_to_the_kwargs_input():
    state = {}
    first = _nested_input_keys("foo_kwargs", state)
    second = _nested_input_keys("bar_kwargs", state)
    assert first == {"data": "foo_kwargs_data"}
    assert second == {"data": "bar_kwargs_data"}
