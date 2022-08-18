from front.state import (
    ConditionNotMet,
    ForbiddenOverwrite,
    ForbiddenWrite,
    State,
    ValueNotSet,
    mk_binder,
)
import pytest


def test_state():

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


def test_binder_simple():
    """This work is to try to add 'auto registering' of bounded variables"""
    d = dict()
    s = mk_binder(state=d)
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


def test_binder(mk_binder=mk_binder):
    """This work is to try to add 'auto registering' of bounded variables"""

    def _test_fresh_state_with_foobar(binder, state):
        assert binder._state == state
        assert state == {}
        assert binder.foo is ValueNotSet
        binder.foo = 42
        assert binder.foo == 42
        assert state == {'foo': 42}
        binder.foo = 496
        assert binder.foo == 496
        assert state == {'foo': 496}
        binder.bar = 8128
        assert state == {'foo': 496, 'bar': 8128}

    # all defaults: no mk_binder arguments: Get a non-exclusive Binder type
    Binder = mk_binder()
    state = dict()
    binder = Binder(state)
    _test_fresh_state_with_foobar(binder, state)

    # give a state to a binder directly get a non-exclusive binder instance.
    state = dict()
    binder = mk_binder(state)
    _test_fresh_state_with_foobar(binder, state)

    # Specify some identifiers, and be only allowed to use those
    Binder = mk_binder(allowed_ids='foo bar')
    state = dict()
    binder = Binder(state)
    _test_fresh_state_with_foobar(binder, state)

    with pytest.raises(AttributeError) as err:
        binder.not_foo
    assert str(err.value) == (
        'That attribute is not in the self._allowed_ids collection: not_foo'
    )

    with pytest.raises(ForbiddenWrite) as err:
        binder.not_foo = -42
    assert str(err.value) == (
        "Can't write there. The id is not in the self._allowed_ids collection: not_foo"
    )

    Binder = mk_binder(allowed_ids='foo bar')
    state = dict()
    binder = Binder(state)

    assert binder._state == state
    assert state == {}
    assert binder.foo is ValueNotSet
    binder.foo = 42
    assert binder.foo == 42
    assert state == {'foo': 42}
    binder.foo = 496
    assert binder.foo == 496
    assert state == {'foo': 496}
    binder.bar = 8128
    assert state == {'foo': 496, 'bar': 8128}

    # TODO: No test of iter here: Should iter reflect state or inclusion list?
    # Here are a few:

    d = dict(gaga=123)
    b = mk_binder(state=d, allowed_ids='foo bar')
    assert list(b) == ['gaga']  # no foo, no bar (should there be?)
    assert b.foo == ValueNotSet
    # still (trying to access non-existing foo, didn't make a difference (should it?):
    assert list(b) == ['gaga']
    b.foo = 42
    assert list(b) == ['gaga', 'foo']
    assert d == {'gaga': 123, 'foo': 42}

    # but though gaga is in the state, and the iter, it's still not accessible through
    # attributes because not in allwed_ids.
    # TODO: What should the behavior actually be?
    with pytest.raises(AttributeError) as err:
        binder.gaga
    assert str(err.value) == (
        'That attribute is not in the self._allowed_ids collection: gaga'
    )

    with pytest.raises(ForbiddenWrite) as err:
        binder.gaga = 'googoo'
    assert str(err.value) == (
        "Can't write there. The id is not in the self._allowed_ids collection: gaga"
    )

    #
    # # give a state to a binder directly get a non-exclusive binder instance.
    # state = dict(foo=42)
    # binder = mk_binder(state)
    # assert binder.foo == 42
    # assert binder.bar == ValueNotSet
    # binder.foo = 1
    # binder.bar = 2
    # assert state == {'foo': 1, 'bar': 2}
    #
    # # Test iteration behavior
    # d = dict(gaga=123)
    # b = mk_binder(state=d)
    # assert list(b) == ['gaga']  # no foo, no bar (should there be?)
    # assert b.foo == ValueNotSet
    # # still (trying to access non-existing foo, didn't make a difference (should it?):
    # assert list(b) == ['gaga']
    # b.foo = 42
    # assert list(b) == ['gaga', 'foo']
    # assert d == {'gaga': 123, 'foo': 42}
    #
    # # Test iteration behavior when we give an inclusion list
