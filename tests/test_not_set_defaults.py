"""``i2``'s ``NotSet`` sentinel in a signature means "required / no default".

See i2mint/i2#48: once ``FuncFactory`` shows ``NotSet`` defaults, front must not
prefill inputs with it, infer an input type from it, or use it as a model default.
These tests use ``i2.deco.NotSet`` directly, so they pass with any i2 version.
"""

from dataclasses import dataclass
from inspect import Parameter

import pytest
from i2 import Sig
from i2.deco import NotSet

from front.elements.elements import (
    FloatInputBase,
    IntInputBase,
    TextInputBase,
    mk_input_element_specs,
)
from front.data_binding import BoundData
from front.py2pydantic import func_to_pyd_model_specs
from front.util import param_default


def _foo(a: int, b: float, c: str, d, e: int = 3):
    return a, b, c, d, e


def _foo_with_not_set():
    """``_foo``'s signature with ``NotSet`` defaults, as a re-landed #88 would show it."""
    sig = Sig(_foo)
    return sig.ch_defaults(
        **{
            name: NotSet
            for name in sig.names
            if sig.parameters[name].default is Parameter.empty
        }
    )(_foo)


def _render_input(cls, param):
    @dataclass
    class Concrete(cls):
        def render(self):
            return self.view_value

    state = {}
    element = Concrete(
        obj=param,
        input_key=f"k_{param.name}",
        bound_data_factory=lambda k: BoundData(k, state),
    )
    return element, state


def test_param_default_maps_not_set_to_empty():
    func = _foo_with_not_set()
    params = Sig(func).parameters
    assert params["a"].default is NotSet  # the fixture really has NotSet defaults
    assert [param_default(p) for p in params.values()] == [Parameter.empty] * 4 + [3]


@pytest.mark.parametrize(
    "cls, name, expected_view",
    [(IntInputBase, "a", 0), (FloatInputBase, "b", 0.0), (TextInputBase, "c", "")],
)
def test_inputs_are_not_prefilled_with_not_set(cls, name, expected_view):
    param = Sig(_foo_with_not_set()).parameters[name]
    element, state = _render_input(cls, param)  # used to raise on int(NotSet)
    assert element.view_value == expected_view
    assert element.value.get() is not NotSet
    assert NotSet not in state.values()


def test_real_defaults_still_prefill():
    param = Sig(_foo_with_not_set()).parameters["e"]
    element, _ = _render_input(IntInputBase, param)
    assert element.view_value == 3


def test_input_specs_do_not_infer_type_from_not_set():
    inputs = {int: {"min_value": 0}, str: {"placeholder": "?"}}
    with_not_set = mk_input_element_specs(_foo_with_not_set(), inputs)
    plain = mk_input_element_specs(_foo, inputs)

    def without_obj(spec):
        return {k: v for k, v in spec.items() if k != "obj"}

    for name in ("a", "b", "c", "d", "e"):
        assert without_obj(with_not_set[name]) == without_obj(plain[name])


def test_pydantic_specs_treat_not_set_as_required():
    specs = dict(func_to_pyd_model_specs(_foo_with_not_set()))
    assert specs == dict(func_to_pyd_model_specs(_foo))
    assert specs["a"] == (int, ...)
    assert specs["e"] == (int, 3)
