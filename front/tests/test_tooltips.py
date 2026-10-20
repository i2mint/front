"""Tests for front.tooltips."""

from front.tooltips import func_tooltip, param_tooltips


def google(a, b):
    """Summary line.

    Second line.
    Third line.
    Fourth line.

    Args:
        a (int): the a
        b: the b
    """


def numpy(a, b):
    """Summary.

    Parameters
    ----------
    a : int
        the a thing
    b : str
        the b
    """


def test_func_tooltip_styles():
    assert func_tooltip(google) == "Summary line."
    assert func_tooltip(google, "first_lines", n_lines=2).endswith("(+more)")
    assert func_tooltip(numpy, "first_lines", n_lines=100).startswith("Summary.")
    assert func_tooltip(lambda: None) == ""


def test_param_tooltips_styles_and_selection():
    assert param_tooltips(google) == {"a": "the a", "b": "the b"}
    assert param_tooltips(numpy) == {"a": "the a thing", "b": "the b"}
    assert param_tooltips(google, include=["a"]) == {"a": "the a"}
    assert param_tooltips(google, exclude=["a"]) == {"b": "the b"}
    assert param_tooltips(google, ledger={"b": "X", "c": "Y"})["b"] == "X"
    assert param_tooltips(lambda a: None) == {}


# --- wiring into specs and elements -----------------------------------------------------

from collections.abc import Callable  # noqa: E402
from functools import partial  # noqa: E402
from typing import Any  # noqa: E402

from front.data_binding import BoundData  # noqa: E402

_STATE = {}

from front import APP_KEY, OBJ_KEY, RENDERING_KEY, AppMaker, SpecMakerBase  # noqa: E402
from front.elements import (  # noqa: E402
    DEFAULT_INPUT_KEY,
    ELEMENT_KEY,
    ExecContainerBase,
    FrontContainerBase,
    InputBase,
    OutputBase,
)
from front.util import dflt_trans  # noqa: E402


class _Page(FrontContainerBase):
    def render(self):
        return {"tooltip": self.tooltip, "children": [c() for c in self.children]}


class _Exec(ExecContainerBase):
    def render(self):
        return self._render_inputs()

    def _noneable(self, input):
        return input


class _In(InputBase):
    def render(self):
        return self.tooltip


class _Out(OutputBase):
    def render(self):
        return None


class _SpecMaker(SpecMakerBase):
    @property
    def _dflt_convention(self):
        return {
            APP_KEY: {"title": "T"},
            OBJ_KEY: {"trans": dflt_trans},
            RENDERING_KEY: {
                ELEMENT_KEY: _Page,
                Callable: {
                    ELEMENT_KEY: _Page,
                    "execution": {
                        ELEMENT_KEY: _Exec,
                        "inputs": {
                            DEFAULT_INPUT_KEY: {
                                ELEMENT_KEY: _In,
                                "bound_data_factory": partial(BoundData, state=_STATE),
                            },
                            Any: {},
                        },
                        "output": {ELEMENT_KEY: _Out},
                    },
                },
            },
        }


def _render(config):
    app = AppMaker(_SpecMaker).mk_app([google], config)
    page = app.children[0]
    return page.tooltip, page.children[0].render()


def test_no_tooltips_unless_asked():
    assert _render({}) == (None, {"a": None, "b": None})


def test_tooltips_flow_into_the_elements():
    config = {RENDERING_KEY: {Callable: {"tooltips": True}}}
    assert _render(config) == ("Summary line.", {"a": "the a", "b": "the b"})


def test_tooltips_config_include_exclude_ledger_and_override_by_name():
    config = {
        RENDERING_KEY: {
            Callable: {"tooltips": {"func": "first_lines", "params": {"exclude": ["b"]}}},
            "google": {"tooltips": {"params": {"exclude": [], "ledger": {"b": "explicit b"}}}},
        }
    }
    func_tip, inputs = _render(config)
    assert func_tip.startswith("Summary line.\nSecond line.") and func_tip.endswith("(+more)")
    assert inputs == {"a": "the a", "b": "explicit b"}  # the by-name spec overrides the type's exclude


def test_explicit_tooltip_in_the_spec_wins_and_func_can_be_switched_off():
    config = {
        RENDERING_KEY: {
            Callable: {"tooltips": {"func": False}},
            "google": {"execution": {"inputs": {"a": {"tooltip": "mine"}}}},
        }
    }
    assert _render(config) == (None, {"a": "mine", "b": "the b"})
