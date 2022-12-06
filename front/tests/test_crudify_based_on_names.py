from front.crude import crudify_based_on_names, prepare_for_crude_dispatch
import pytest
from functools import partial


@pytest.fixture
def foo():
    def inner(x, y):
        return x + y

    return inner


@pytest.fixture
def bar():
    def inner(a, x):
        return a * x

    return inner


def test_param_to_mall_map(foo, bar):
    general_crudifier = partial(
        crudify_based_on_names,
        param_to_mall_map={'x': 'x_store'},
        crudifier=partial(
            prepare_for_crude_dispatch,
            mall={'x_store': {'stored_two': 2, 'stored_four': 4}},
        ),
    )

    foo, bar = map(general_crudifier, [foo, bar])

    assert foo('stored_two', 10) == 12
    assert bar(4, 'stored_four') == 16


def test_func_output_store(foo, bar):
    general_crudifier = partial(
        crudify_based_on_names,
        func_output_store={'foo': 'foo_store'},
        crudifier=partial(prepare_for_crude_dispatch, mall={'foo_store': {}},),
    )

    foo = map(general_crudifier, [foo])

    assert True
    # print(mall)
    # assert bar(4, "stored_four") == 16
