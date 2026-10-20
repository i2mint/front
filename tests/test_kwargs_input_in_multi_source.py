"""A kwargs input can be one of the sources of a multi-source input.

Regression test for i2mint/front#45: such a kwargs input got no nested ``inputs``
(the section only fed the input of the ``kwargs`` parameter), so its nested inputs
had no ``bound_data_factory`` and no element for their types, and the app failed as
soon as that source was rendered.
"""

from dataclasses import dataclass

from i2 import Sig

from front.data_binding import BoundData
from front.elements.elements import (
    DEFAULT_INPUT_KEY,
    ELEMENT_KEY,
    ExecContainerBase,
    IntInputBase,
    KwargsInputBase,
    MultiSourceInputBase,
    OutputBase,
    TextInputBase,
)


@dataclass
class _Text(TextInputBase):
    def render(self):
        return self.view_value


@dataclass
class _OtherText(_Text):
    pass


@dataclass
class _Int(IntInputBase):
    def render(self):
        return self.view_value


@dataclass
class _Out(OutputBase):
    def render(self):
        return self.output


class _Section(ExecContainerBase):
    def render(self):
        return self._render_inputs()

    def _noneable(self, input):
        return input


@dataclass
class _Kwargs(KwargsInputBase):
    """Renders its nested inputs the way a front implementation does: as a section."""

    def render(self):
        section = _Section(
            obj=self.get_kwargs, inputs=self.inputs, output={ELEMENT_KEY: _Out}
        )
        self._nested_section = section
        return section()


class _Multi(MultiSourceInputBase):
    source = None

    def render(self):
        source = next(c for c in self.input_components if c.name == self.source)
        return source()


def _params(a: int = 1, b: str = "x"):
    """The signature of the kwargs source."""


def f(data):
    return data


def _section(state, *, multi_spec=None):
    multi_spec = multi_spec or {
        ELEMENT_KEY: _Multi,
        "From text": {ELEMENT_KEY: _Text},
        "From params": {ELEMENT_KEY: _Kwargs, "func_sig": Sig(_params)},
    }
    inputs = {
        "data": multi_spec,
        int: {ELEMENT_KEY: _Int},
        str: {ELEMENT_KEY: _Text},
        DEFAULT_INPUT_KEY: {"bound_data_factory": lambda k: BoundData(k, state)},
    }
    return _Section(obj=f, inputs=inputs, output={ELEMENT_KEY: _Out})


def _multi_input(section):
    return next(c for c in section.children if isinstance(c, MultiSourceInputBase))


def test_kwargs_source_of_a_multi_source_input_renders_its_nested_inputs():
    state = {}
    multi = _multi_input(_section(state))
    multi.source = "From params"
    assert multi() == {"a": 1, "b": "x"}

    kwargs_input = next(c for c in multi.input_components if c.name == "From params")
    nested = {c.obj.name: c for c in kwargs_input._nested_section.children[:-1]}
    assert {name: type(c) for name, c in nested.items()} == {"a": _Int, "b": _Text}
    # nested keys are scoped to the multi-source input (i2mint/front#40)
    assert {c.input_key for c in nested.values()} == {"f_data_a", "f_data_b"}


def test_the_multi_source_spec_is_not_nested_into_its_kwargs_source():
    multi = _multi_input(_section({}))
    kwargs_input = next(c for c in multi.input_components if c.name == "From params")
    assert "data" not in kwargs_input.inputs
    assert int in kwargs_input.inputs and DEFAULT_INPUT_KEY in kwargs_input.inputs


def test_own_nested_inputs_of_the_kwargs_source_win():
    multi_spec = {
        ELEMENT_KEY: _Multi,
        "From params": {
            ELEMENT_KEY: _Kwargs,
            "func_sig": Sig(_params),
            "inputs": {"b": {ELEMENT_KEY: _OtherText}},
        },
    }
    multi = _multi_input(_section({}, multi_spec=multi_spec))
    multi.source = "From params"
    multi()
    kwargs_input = multi.input_components[0]
    nested = {c.obj.name: c for c in kwargs_input._nested_section.children[:-1]}
    assert type(nested["b"]) is _OtherText
