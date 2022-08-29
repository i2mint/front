"""Naive stash of VF proposals for binding"""

from dataclasses import dataclass
from typing import (
    Protocol,
    KT,
    VT,
    Mapping,
    Union,
    Callable,
    Iterable,
    MutableMapping,
    Optional,
)
from functools import partial


#########################################################################################
# Binding (Proposals)
#########################################################################################

from typing import Protocol, MutableMapping, runtime_checkable
from functools import partial

from i2 import mk_sentinel, ensure_identifiers


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


# from typing import Iterable, Callable, MutableMapping, Union
from typing import NewType

from i2 import ensure_identifiers

StateType = NewType('StateType', MutableMapping)
Identifier = NewType('Identifier', str)
Identifiers = Union[Iterable[Identifier], str]
StateFactory = Callable[[Identifiers], StateType]


@dataclass
class Binder:
    _reserved_vars = {'_state', '_factory', '_container'}

    def __init__(self, state: StateType, factory: Callable, container: type):
        self._state = state
        self._factory = factory
        self._container = container

    def __getattr__(self, k):
        if k not in self._container.__dict__:
            setattr(self._container, k, self._factory(k))
        c = self._container(self._state)
        return getattr(c, k)

    def __setattr__(self, k, v):
        # Need this "not _state, _factory or _container", or the __init__ won't be
        # able to set
        # _state, _factory and _container
        if k in self._reserved_vars:
            self.__dict__[k] = v
        else:
            # Call getattr on self only to make sure that the descriptor has been
            # created.
            getattr(self, k)
            c = self._container(self._state)
            setattr(c, k, v)

    def __iter__(self):
        yield from self._container._state


def mk_binder(
    *identifiers: Identifiers, state: StateType, bound_val_factory=BoundVal,
):
    """

    :param identifiers:
    :param bound_val_factory:
    :return:

    >>> Binder = mk_binder('foo bar')
    >>> d = dict()
    >>> b = Binder(d)

    We ``b.foo`` exists, but is not set.

    >>> b.foo
    ValueNotSet

    So let's set it:

    >>> b.foo = 42
    >>> b.foo
    42

    So ``b.foo`` is now set, but the real point is that this assignment was "registered"
    in the state we give the ``Binder``:

    >>> d
    {'foo': 42}

    Wanna see that again?

    >>> b.foo = "I'm bound"
    >>> b.foo
    "I'm bound"
    >>> d
    {'foo': "I'm bound"}

    And same with ``b.bar``:

    >>> b.bar
    ValueNotSet
    >>> b.bar = "me too"
    >>> b.bar
    'me too'
    >>> d
    {'foo': "I'm bound", 'bar': 'me too'}

    A ``Binder`` will also have some useful mapping methods that are linked to the
    underlying ``state``.

    >>> Binder = mk_binder('the', 'variables', 'I', 'want')
    >>> state = dict()
    >>> b = Binder(state)
    >>> list(b)
    []
    >>> b.want  # I see a want, but no value is set
    ValueNotSet
    >>> list(b)  # list still gives me nothing
    []
    >>> b.want = 42  # but if I set a value for want
    >>> list(b)  # I see want in the list
    ['want']
    >>> 'want' in b  # I can do this too
    True
    >>> 'not_in_there' in b
    False
    >>> 'variables' in b  # 'variables' not "there" because not set
    False


    """
    identifiers = ensure_identifiers(*identifiers)

    @dataclass
    class BoundValContainer:
        _state: MutableMapping

    for id_ in identifiers:
        setattr(BoundValContainer, id_, bound_val_factory(id_))

    return Binder(state=state, factory=bound_val_factory, container=BoundValContainer)
