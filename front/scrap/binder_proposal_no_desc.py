from dataclasses import dataclass
from functools import partial
from typing import MutableMapping, NewType, Protocol, runtime_checkable

from i2.util import mk_sentinel
from i2 import Sig

StateType = NewType('StateType', MutableMapping)


@runtime_checkable
class HasState(Protocol):
    _state: MutableMapping


_mk_sentinel = partial(
    mk_sentinel, boolean_value=False, repr_=lambda x: x.__name__, module=__name__
)
ValueNotSet, Empty = map(_mk_sentinel, ['ValueNotSet', 'Empty'])


class BoundVal:
    def __init__(self, key, *, value_not_set=ValueNotSet):
        self.key = key
        self.value_not_set = value_not_set

    def __repr__(self):
        if isinstance(self.key, str):
            key_str = f"'{self.key}'"
        else:
            key_str = self.key
        return f'{type(self).__name__}({key_str})'

    def _get_(self, obj: HasState, objtype=None):
        if obj is None:
            return self
        return obj._state.get(self.key, self.value_not_set)

    def _set_(self, obj: HasState, value):
        obj._state[self.key] = value
        self.something = value

    __get__ = _get_
    __set__ = _set_


@dataclass
class Binder:
    _state: StateType
    _value_not_set = ValueNotSet

    def __post_init__(self):
        sig = Sig(self.__init__)
        self._reserved_keys = sig.names

    def __getattr__(self, k):
        self._ensure_reserved_keys()
        if k not in self.__dict__['_reserved_keys']:
            return self._state.get(k, self._value_not_set)
        return self.__dict__[k]

    def __setattr__(self, k, v):
        self._ensure_reserved_keys()
        if k not in self._reserved_keys:
            self._state[k] = v
        else:
            self.__dict__[k] = v

    def _ensure_reserved_keys(self):
        if '_reserved_keys' not in self.__dict__:
            self.__dict__['_reserved_keys'] = Sig(self.__init__).names + [
                '_reserved_keys'
            ]


def test_binder_simple():
    """This work is to try to add 'auto registering' of bounded variables"""
    d = dict()
    s = Binder(_state=d)
    assert d == {}
    assert s.foo is ValueNotSet
    s.foo = 42
    assert s.foo == 42
    assert d == {'foo': 42}
    s.foo = 496
    assert s.foo == 496
    assert d == {'foo': 496}
    s.bar = 8128
    assert d == {'foo': 496, 'bar': 8128}
