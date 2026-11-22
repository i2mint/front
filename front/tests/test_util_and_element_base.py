"""Tests for ``front.util`` helpers and the framework-agnostic ``front.elements`` base classes."""

from dataclasses import dataclass
from inspect import Parameter

import pytest

from front.elements.elements import (
    ELEMENT_KEY,
    FrontElementBase,
    mk_element_from_spec,
)
from front.util import (
    deep_merge,
    dflt_name_trans,
    get_value,
    incremental_str_maker,
    iterable_to_enum,
    normalize_map,
    obj_name,
    param_default,
    subdict,
)


def test_param_default_treats_placeholders_as_no_default():
    from i2.deco import NotSet

    assert param_default(Parameter("x", Parameter.KEYWORD_ONLY, default=3)) == 3
    assert param_default(Parameter("x", Parameter.KEYWORD_ONLY, default=NotSet)) is (
        Parameter.empty
    )
    assert param_default(Parameter("x", Parameter.KEYWORD_ONLY)) is Parameter.empty


def test_subdict_follows_keys_order_and_ignores_missing():
    assert subdict({"a": 1, "b": 2}, ["b", "zzz", "a"]) == {"b": 2, "a": 1}
    assert subdict({"a": 1}) == {}


def test_iterable_to_enum():
    E = iterable_to_enum([1, "two"], name="E")
    assert E.__name__ == "E"
    assert E["1"].value == 1 and E["two"].value == "two"


def test_get_value_and_normalize_map():
    assert get_value(5) == 5
    assert get_value(lambda a, b: a + b, 1, 2) == 3
    assert normalize_map(None) == {}
    assert normalize_map({"a": 1}) == {"a": 1}
    assert normalize_map(lambda: {"b": 2}) == {"b": 2}


def test_deep_merge_does_not_mutate_inputs():
    a = {"x": {"y": 1}, "k": 1}
    b = {"x": {"z": 2}, "k": {"now": "a dict"}}
    assert deep_merge(a, b) == {"x": {"y": 1, "z": 2}, "k": {"now": "a dict"}}
    assert a == {"x": {"y": 1}, "k": 1}
    assert b == {"x": {"z": 2}, "k": {"now": "a dict"}}


def test_incremental_str_maker():
    mk = incremental_str_maker("item{:02d}")
    assert [mk(), mk(), mk()] == ["item01", "item02", "item03"]


def test_obj_name_and_dflt_name_trans():
    def my_func():
        pass

    assert obj_name(my_func) == "my_func"
    n1, n2 = obj_name(lambda: 0), obj_name(lambda: 0)
    assert n1.startswith("UnnamedObject") and n1 != n2
    assert dflt_name_trans(my_func) == "My Func"
    assert dflt_name_trans("some_string_name") == "Some String Name"


@dataclass
class _Hello(FrontElementBase):
    log: list = None

    def pre_render(self):
        self.log.append("pre")

    def render(self):
        self.log.append("render")
        return f"hello {self.name}"

    def post_render(self, render_result):
        self.log.append("post")
        return render_result.upper()


def test_element_lifecycle_order_and_display_flag():
    log = []
    assert _Hello(name="w", log=log)() == "HELLO W"
    assert log == ["pre", "render", "post"]

    log.clear()
    assert _Hello(name="w", log=log, display=False)() is None
    assert log == []


def test_name_and_display_may_be_callables_of_obj():
    log = []
    el = _Hello(obj=len, name=lambda o: o.__name__, display=lambda o: True, log=log)
    assert el.name == "len" and el.display is True
    assert _Hello(log=log).name == ""  # no name: empty string


def test_abstract_base_cannot_be_instantiated():
    with pytest.raises(TypeError):
        FrontElementBase()


def test_mk_element_from_spec():
    log = []
    el = mk_element_from_spec({ELEMENT_KEY: _Hello, "name": "x", "log": log})
    assert el() == "HELLO X"
    with pytest.raises(RuntimeError, match=ELEMENT_KEY):
        mk_element_from_spec({"name": "x"})


def test_mk_element_from_spec_reports_factory_errors(capsys):
    def bad_factory(**kw):
        raise ZeroDivisionError

    with pytest.raises(ZeroDivisionError):
        mk_element_from_spec({ELEMENT_KEY: bad_factory})
    assert "error occurred when trying to build element" in capsys.readouterr().out
