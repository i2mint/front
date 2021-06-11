import os
from typing import Dict
import pandas as pd


def make_a_table_of_ints(col_name: str = 'integers', **keys_and_values: Dict[str, int]):
    return pd.Series(data=keys_and_values, name=col_name)


def make_a_table_of_floats(
    col_name: str = 'floats', **keys_and_values: Dict[str, float]
):
    return pd.Series(data=keys_and_values, name=col_name)


def make_a_table_of_strs(col_name: str = 'strings', **keys_and_values: Dict[str, str]):
    return pd.Series(data=keys_and_values, name=col_name)


def make_a_table_of_bools(
    col_name: str = 'booleans', **keys_and_values: Dict[str, bool]
):
    return pd.Series(data=keys_and_values, name=col_name)


funcs = [
    make_a_table_of_ints,
    make_a_table_of_floats,
    make_a_table_of_strs,
    make_a_table_of_bools,
]

if __name__ == '__main__':
    from front.base import dispatch_funcs
    from front.page_funcs import KeywordArgsPageFunc

    print('file: {}'.format(os.path.realpath(__file__)))

    app = dispatch_funcs(funcs, configs={'page_factory': KeywordArgsPageFunc})

    app()
