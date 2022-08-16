from dataclasses import dataclass
from typing import Protocol, KT, VT, Mapping, Union, Callable, Iterable, MutableMapping
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


def test_state():
    import pytest

    st_state = dict()

    st_state['_front'] = dict()  # carve out a place to put front state

    state = State(
        state=st_state['_front'],
        forbidden_writes={'foo'},
        forbidden_overwrites={'apple', 'banana'},
        condition_for_key={'apple': list, 'carrot': lambda x: x > 10},
    )

    assert state != dict()  # it's not an empty dict
    # but you can retrieve the dict of key-value pairs, which will be an empty dict
    assert dict(state) == dict()

    with pytest.raises(ForbiddenWrite):
        state['foo'] = 42

    with pytest.raises(ValueError) as err:
        state['apple'] = 42

    assert (
        str(err.value) == 'The value for the apple key must satisfy condition '
        "IsInstanceOf(class_or_tuple=<class 'list'>)"
    )

    state['apple'] = [4, 2]

    with pytest.raises(ForbiddenOverwrite) as err:
        state['apple'] = [4, 2, 1]

    assert str(err.value) == 'Not allowed to write under this key more than once: apple'

    # but this works since I'm trying to write the same value (just ignores it)
    state['apple'] = [4, 2]

    with pytest.raises(ConditionNotMet) as err:
        state['carrot'] = 10

    assert str(err.value)[:62] == (
        'The value for the carrot key must satisfy condition <function '
    )

    state['carrot'] = 11  # the value is > 10 so okay!
    state['carrot'] = 12  # overwrites allowed

    assert dict(state) == {'apple': [4, 2], 'carrot': 12}

    # We give you a .get since you can always have one when you have a ``__getitem__``:
    assert state.get('carrot') == 12
    assert state.get('key_that_does_not_exist', 'my_default') == 'my_default'

    # And then, we'll forward other MutableMapping operations to the underlying state,
    # so if it can handle them, you'll get those too!
    assert len(state) == 2
    assert list(state) == ['apple', 'carrot']
    assert list(state.items()) == [('apple', [4, 2]), ('carrot', 12)]
    assert 'apple' in state
    assert 'kiwi' not in state
