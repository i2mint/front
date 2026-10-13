"""``dflt_trans`` gives nameless objects names that are the same on every rerun."""

from functools import partial

from front.util import dflt_trans


def _named(c):
    return c


def _mk_objs():
    return [lambda a: a, _named, lambda b: b, partial(_named)]


def _names(objs):
    return [o.__name__ for o in dflt_trans(objs)]


def test_names_are_stable_across_reruns():
    assert _names(_mk_objs()) == _names(_mk_objs())
    assert _names(_mk_objs())[:3] == ["UnnamedObject001", "_named", "UnnamedObject002"]


def test_unnamed_names_skip_names_in_use():
    def UnnamedObject001():
        pass

    names = _names([lambda: 1, UnnamedObject001])
    assert names == ["UnnamedObject002", "UnnamedObject001"]


def test_accepts_any_iterable():
    assert _names(iter([lambda: 1])) == ["UnnamedObject001"]
