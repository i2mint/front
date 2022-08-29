from dataclasses import dataclass
from functools import partial

from front.state import GetterSetter, State, StateType
from i2 import Sig
from i2.util import mk_sentinel

_mk_sentinel = partial(mk_sentinel, repr_=lambda x: x.__name__, module=__name__)
ValueNotSet, Empty = map(_mk_sentinel, ['ValueNotSet', 'Empty'])


class BoundData:
    def __init__(self, id: str, state: GetterSetter):
        self.id = id
        self.state = State(state=state, forbidden_writes={ValueNotSet})

    def get(self):
        return self.state.get(self.id, ValueNotSet)

    def set(self, value):
        self.state[self.id] = value

    __call__ = get


@dataclass
class Binder:
    front_state: StateType
    bound_data_factory = BoundData

    def __post_init__(self):
        sig = Sig(self.__init__)
        self._reserved_keys = sig.names

    def __getattr__(self, k):
        self._ensure_reserved_keys()
        if k not in self.__dict__['_reserved_keys']:
            setattr(self, k, Empty)
        return self.__dict__[k]

    def __setattr__(self, k, v):
        self._ensure_reserved_keys()
        if k in self.__dict__['_reserved_keys']:
            self.__dict__[k] = v
        else:
            bound_data = self.bound_data_factory(k, self.front_state)
            if v is not Empty:
                bound_data.set(v)
            self.__dict__[k] = bound_data

    def _ensure_reserved_keys(self):
        if '_reserved_keys' not in self.__dict__:
            self.__dict__['_reserved_keys'] = Sig(self.__init__).names + [
                '_reserved_keys'
            ]
