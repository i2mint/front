"""``SelectorBase`` options may be a sequence, a mapping (its keys, e.g. a mall) or a
callable returning either (i2mint/streamlitfront#2)."""

from dataclasses import dataclass
from inspect import Parameter

import pytest

from front.data_binding import BoundData
from front.elements import SelectorBase


@dataclass
class _Selector(SelectorBase):
    def render(self):
        return self.view_value


def _selector(options, **kwargs):
    state = {}
    return _Selector(
        obj=Parameter("wf_src", Parameter.POSITIONAL_OR_KEYWORD),
        name="wf_src",
        input_key="wf_src",
        bound_data_factory=lambda key: BoundData(key, state=state),
        options=options,
        **kwargs,
    )


@pytest.mark.parametrize(
    "options",
    [
        {"wfsrc": "my text", "other": 1},  # a mapping (a mall): its keys
        lambda: {"wfsrc": "my text", "other": 1},  # a callable returning one
        ["wfsrc", "other"],
        lambda: ("wfsrc", "other"),
    ],
)
def test_options_of_any_kind_give_the_first_key_as_default(options):
    s = _selector(options)
    s.pre_render()
    assert s.view_value == "wfsrc"
    assert s._options == ["wfsrc", "other"]


def test_empty_options():
    s = _selector({})
    s.pre_render()
    assert s._options == [] and s.view_value is None
