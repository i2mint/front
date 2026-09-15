"""Data-binding primitives that connect front element values to a backing state store.

A :class:`BoundData` wraps a keyed slot in a :class:`~front.state.State` so an
element can read and write its current value through a single object. The
``ValueNotSet`` / ``Empty`` sentinels distinguish "no value yet" from a
deliberate empty value.
"""

from dataclasses import dataclass
from functools import partial

from front.state import GetterSetter, State, StateType
from i2 import Sig
from i2.util import mk_sentinel

_mk_sentinel = partial(mk_sentinel, repr_=lambda x: x.__name__, module=__name__)
ValueNotSet, Empty = map(_mk_sentinel, ["ValueNotSet", "Empty"])


class BoundData:
    """A read/write handle on one key (``id``) of a state mapping.

    ``get`` returns ``ValueNotSet`` while the key is absent; ``set`` writes through
    to the state. Calling the instance is the same as ``get``.

    >>> state = {}
    >>> bound = BoundData('x', state)
    >>> bound.get()
    ValueNotSet
    >>> bound.set(3)
    >>> bound(), state
    (3, {'x': 3})

    See Also:
        ``Binder``: makes ``BoundData`` handles on demand, as attributes.
    """

    def __init__(self, id: str, state: GetterSetter):
        self.id = id
        self.state = State(state=state, forbidden_writes={ValueNotSet})

    def get(self):
        """Return the value stored under ``id``, or ``ValueNotSet``."""
        return self.state.get(self.id, ValueNotSet)

    def set(self, value):
        """Write ``value`` under ``id`` in the state."""
        self.state[self.id] = value

    __call__ = get


@dataclass
class Binder:
    """Expose keys of ``front_state`` as attributes (or items) that are ``BoundData`` handles.

    Reading an unknown attribute creates a handle for that key (without writing to
    the state); assigning to it creates the handle and writes the value.

    >>> state = {}
    >>> b = Binder(state)
    >>> b.foo.get()
    ValueNotSet
    >>> b.foo = 42
    >>> b.foo(), state
    (42, {'foo': 42})
    >>> b['bar'] = 'hi'
    >>> state
    {'foo': 42, 'bar': 'hi'}

    See Also:
        ``front.state.mk_binder``: a descriptor-based variant with an allow-list of names.
    """

    front_state: StateType
    bound_data_factory = BoundData

    def __post_init__(self):
        sig = Sig(self.__init__)
        self._reserved_keys = sig.names

    def __getattr__(self, k):
        self._ensure_reserved_keys()
        if k not in self.__dict__["_reserved_keys"]:
            setattr(self, k, Empty)
        return self.__dict__[k]

    def __setattr__(self, k, v):
        self._ensure_reserved_keys()
        if k in self.__dict__["_reserved_keys"]:
            self.__dict__[k] = v
        else:
            bound_data = self.bound_data_factory(k, self.front_state)
            if v is not Empty:
                bound_data.set(v)
            self.__dict__[k] = bound_data

    def _ensure_reserved_keys(self):
        if "_reserved_keys" not in self.__dict__:
            self.__dict__["_reserved_keys"] = Sig(self.__init__).names + [
                "_reserved_keys"
            ]

    __getitem__ = __getattr__
    __setitem__ = __setattr__
