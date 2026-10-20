"""An exec section must not mutate the (shared) input spec it is given.

Regression test for i2mint/front#39: ``_feed_kwargs_input_spec`` used to assign
into ``inputs["kwargs"]["inputs"]``, which is the dict held by a convention
default, so one app's input specs leaked into every app built afterwards.
"""

import copy
from dataclasses import dataclass

from front.data_binding import BoundData
from front.elements.elements import (
    DEFAULT_INPUT_KEY,
    ELEMENT_KEY,
    ExecContainerBase,
    OutputBase,
    TextInputBase,
)


@dataclass
class _Text(TextInputBase):
    def render(self):
        return self.view_value


@dataclass
class _Out(OutputBase):
    def render(self):
        return self.output


class _Section(ExecContainerBase):
    def render(self):
        return None

    def _noneable(self, input):
        return input


def _shared_inputs(state):
    """Like a convention default: a ``kwargs`` entry that is always present."""
    return {
        "kwargs": {ELEMENT_KEY: _Text},
        str: {ELEMENT_KEY: _Text},
        DEFAULT_INPUT_KEY: {"bound_data_factory": lambda k: BoundData(k, state)},
    }


def test_exec_section_does_not_mutate_the_shared_inputs_spec():
    state = {}
    shared = _shared_inputs(state)
    snapshot = copy.copy(shared["kwargs"])

    def first(a: str):
        return a

    def second(b: str):
        return b

    first_section = _Section(
        obj=first,
        inputs=dict(shared, a={"disabled": True}),
        output={ELEMENT_KEY: _Out},
    )
    _Section(obj=second, inputs=dict(shared), output={ELEMENT_KEY: _Out})

    assert shared["kwargs"] == snapshot  # nothing written into the shared default
    # ... while each section still sees its own siblings under the kwargs spec
    assert first_section.inputs["kwargs"]["inputs"]["a"] == {"disabled": True}
