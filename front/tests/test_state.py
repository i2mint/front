from front.state import ConditionNotMet, ForbiddenOverwrite, ForbiddenWrite, State


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
