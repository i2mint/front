"""Test combinations of objects of different modules"""


def foo(a, b):
    return a * b


def test_prepare_for_crude_dispatch_and_variations():
    from i2 import Sig

    # ------------ With prepare_for_crude_dispatch ----------

    from front.crude import prepare_for_crude_dispatch

    mall = {'a_store': {'one': 1, 'two': 2}, 'saves': {}}

    bar = prepare_for_crude_dispatch(
        foo,
        param_to_mall_map={'a': 'a_store'},
        mall=mall,
        output_store=mall['saves'],
        include_stores_attribute=True,
    )

    assert str(Sig(bar)) == "(a: str, b, save_name: str = '')"
    assert bar('two', 'mice', save_name='save_here') == 'micemice'

    assert bar.store_for_param == {'a': {'one': 1, 'two': 2}}
    assert bar.output_store == {'save_here': 'micemice'}

    # ------------ With prepare_for_dispatch (prepare_for_crude_dispatch + enum) ----------

    from front.base import prepare_for_dispatch

    mall = {'a_store': {'one': 1, 'two': 2}, 'saves': {}}

    bar = prepare_for_dispatch(
        foo,
        param_to_mall_map={'a': 'a_store'},
        mall=mall,
        output_store=mall['saves'],
        #     include_stores_attribute=True,
    )

    class FakeEnum:
        value = 'two'

    assert str(Sig(bar)) == "(a: front.util.a_enum, b, save_name: str = '')"

    assert bar(FakeEnum, 'mice', save_name='save_here') == 'micemice'
