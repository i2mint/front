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
