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
    Container,
)
from functools import partial


class Forbidden(Exception):
    """To use to indicate that something is not allowed"""


class ForbiddenWrite(Forbidden):
    """Error to raise when a write operation is not allowed"""


class ForbiddenOverwrite(Forbidden):
    """Error to raise when a writes to existing keys are not allowed"""


class ConditionNotMet(ValueError):
    """Raised when a value doesn't meet some condition"""


class GetterSetter(Protocol):
    """The type of an object ``obj`` that has the operations ``v = obj[k]`` and ``obj[
    k] = v``"""

    def __getitem__(self, k: KT) -> VT:
        pass

    def __setitem__(self, k: KT, v: VT):
        pass


KeyFilterFunc = Callable[[KT], bool]


@dataclass
class IsInstanceOf:
    class_or_tuple: Union[type, Iterable[type]]

    def __call__(self, obj):
        return isinstance(obj, self.class_or_tuple)


def _if_type_mk_filter_func(x):
    if isinstance(x, type):
        return IsInstanceOf(x)
    return x


# TODO: forbidden_writes and forbidden_overwrites could be boolean functions instead (
#  cast from iterable automatically for convenience)
@dataclass
class State(MutableMapping):
    state: GetterSetter
    condition_for_key: Mapping[KT, Union[KeyFilterFunc, type]] = ()
    forbidden_writes: Iterable[KT] = ()
    forbidden_overwrites: Iterable[KT] = ()

    def __post_init__(self):
        self.condition_for_key = {
            k: _if_type_mk_filter_func(v)
            for k, v in dict(self.condition_for_key).items()
        }
        self.forbidden_overwrites = set(self.forbidden_overwrites)
        self.forbidden_writes = set(self.forbidden_writes)

    def __getitem__(self, k):
        return self.state[k]

    def get(self, k, default=None):
        if k in self.state:
            return self.state[k]
        else:
            return default

    def __setitem__(self, k, v):
        if k in self.forbidden_writes:
            raise ForbiddenWrite(f'Not allowed to write on {k}')
        if k in self.forbidden_overwrites and k in self.state and self.state[k] != v:
            raise ForbiddenOverwrite(
                f'Not allowed to write under this key more than once: {k}'
            )
        if k in self.condition_for_key and not self.condition_for_key[k](v):
            raise ConditionNotMet(
                f'The value for the {k} key must satisfy condition '
                f'{self.condition_for_key[k]}'
            )
        self.state[k] = v

    def __repr__(self):
        return repr(self.state)

    # Adding other dunders that forward to self.state (so they'll work if state
    # dunders do)
    def __len__(self):
        return len(self.state)

    def __contains__(self, k):
        return k in self.state

    def __iter__(self):
        return iter(self.state)

    def __delitem__(self, k):
        del self.state[k]


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

DFLT_BOUND_VAL_FACTORY = BoundVal


class _Binder:
    _reserved_vars = {'_state', '_factory'}

    def __init__(self, state: StateType, factory=DFLT_BOUND_VAL_FACTORY):
        self._state = state
        self._factory = factory

    def __iter__(self):
        yield from self._state

    __dir__ = __iter__


class _DynamicBindsMixin:
    """
    Intercepts attribute operations, using a binder descriptor as their values.
    Uses ``_factory`` attribute to make the descriptors for a given attribute name.
    """

    def __getattr__(self, k):
        if k not in self.__dict__:
            setattr(type(self), k, self._factory(k))
        return getattr(self, k)

    def __setattr__(self, k, v):
        # Need this "not in _reserved_vars", otherwise the __init__ won't be able to set
        # _state and _factory
        if k not in self._reserved_vars:
            self.__dict__['_state'][k] = v
        self.__dict__[k] = v  # put it in the __dict__ (so it becomes an attribute)


class _ExclusiveBindsMixin(_DynamicBindsMixin):
    """
    To auto-creational functionalities of _DynamicBindsMixin, adds the restriction
    that this can only be done for a given set of names (as specified by the
    ``._allowed_ids`` attribute
    """

    _allowed_ids: Container = ()

    def __getattr__(self, k):
        if k in self.__dict__ or k in self._allowed_ids:
            return super().__getattr__(k)
        else:
            raise AttributeError(
                f'That attribute is not in the self._allowed_ids collection: {k}'
            )

    def __setattr__(self, k, v):
        if k in self._reserved_vars or k in self._allowed_ids:
            return super().__setattr__(k, v)
        else:
            raise ForbiddenWrite(
                "Can't write there. The id is not in the self._allowed_ids collection"
                f': {k}'
            )


def _ensure_allowed_ids(allowed_ids):
    if isinstance(allowed_ids, str):
        allowed_ids = ensure_identifiers(allowed_ids)
    else:
        allowed_ids = ensure_identifiers(*allowed_ids)

    assert not isinstance(allowed_ids, str)
    return allowed_ids


def mk_binder(
    state: Optional[StateType] = None,
    allowed_ids: Optional[Identifiers] = None,
    bound_val_factory: Callable = DFLT_BOUND_VAL_FACTORY,
):
    """
    >>> Binder = mk_binder()
    >>> d = dict()
    >>> b = Binder(d)

    If I ask for ``b.foo`` (or any valid python identifier I want) it'll be inserted
    as an "descriptor" attribute of ``Binder``, but it's  value will be special value
    ``ValueNotSet``.

    >>> b.foo
    ValueNotSet
    >>> 'foo' in dir(Binder)
    True

    Let's set the value of ``foo```:

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

    >>> Binder = mk_binder(allowed_ids=['the', 'variables', 'I', 'want'])
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

    # TODO: Make it pickalble! (add reduce? Make base outside function?)

    if allowed_ids is None:

        class DynamicBinder(_Binder, _DynamicBindsMixin):
            """Specific Binder with dynamic on-the-fly identifiers"""

        Binder = DynamicBinder

    else:

        class ExclusiveBinder(_Binder, _ExclusiveBindsMixin):
            """Specific Binder with exclusive identifiers"""

            _allowed_ids = set(_ensure_allowed_ids(allowed_ids))

        for id_ in ExclusiveBinder._allowed_ids:
            setattr(ExclusiveBinder, id_, bound_val_factory(id_))

        Binder = ExclusiveBinder

    # TODO: Should we really be having the function return type or instance thereof
    #  according to whether state is given?
    if state is not None:
        return Binder(state=state)
    else:
        return Binder
