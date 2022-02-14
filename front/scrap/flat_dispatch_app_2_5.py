import streamlit_pydantic as sp
import streamlit as st
from typing_extensions import TypedDict
from pydantic import create_model_from_typeddict
from enum import Enum


mall = {'x': {'xs_1': 3, 'xs_2': 5}, 'fvs': {'fv_1': [1, 2, 3], 'fv_2': [4, 5, 6]}}


def mk_Enum_from_store(store, key):
    choices = store[key].keys()
    choice = Enum(f'DynamicEnum_{key}', {item: item for item in choices})
    return choice


def mk_Input_for_store_keys(store, keys):
    vals = {key: mk_Enum_from_store(store, key) for key in keys}
    choices_dict = TypedDict('Choices', vals)
    Input = create_model_from_typeddict(choices_dict)

    return Input


my_input = mk_Input_for_store_keys(store=mall, keys=['x', 'fvs'])

data = sp.pydantic_input(key='my_form', model=my_input)
if data:
    st.write(data)
