import streamlit_pydantic as sp
import streamlit as st
from typing_extensions import TypedDict
from pydantic import create_model_from_typeddict
from enum import Enum
from dol import Files

rootdir = "/Users/sylvain/Desktop/stuff"

# mall = {'x': {'xs_1': 3, 'xs_2': 5}, 'fvs': {'fv_1': [1, 2, 3], 'fv_2': [4, 5, 6]}}

mall = {
    "x": {"xs_1": 3, "xs_2": 5},
    "fvs": {"fv_1": [1, 2, 3], "fv_2": [4, 5, 6]},
    "files": Files(rootdir),
}


def mk_Enum_from_store(store, key):  # no caps in funcs
    choices = store[key].keys()
    choice = Enum(f'DynamicEnum_{key}', {item: item for item in choices})
    return choice


# differentiate between store and mall

# may be replace (store, keys) by a simple dict
def mk_Input_for_store_keys(store, keys):
    vals = {key: mk_Enum_from_store(store, key) for key in keys}
    choices_dict = TypedDict('Choices', vals)
    Input = create_model_from_typeddict(choices_dict)

    return Input


# <<<<<<< HEAD
# class Input(BaseModel):
#     x:dict
#     fvs: dict

my_keys = list(mall)
my_input = mk_Input_for_store_keys(store=mall, keys=my_keys)

data = sp.pydantic_form(key="my_form", model=my_input)
# =======
# my_input = mk_Input_for_store_keys(store=mall, keys=['x', 'fvs'])
#
# data = sp.pydantic_input(key='my_form', model=my_input)
# >>>>>>> 5453239b595c0f0700cc2b224e3cde1ca75c52fa
if data:
    st.write(data)

# InputObject -> (args, kwargs)-- func --> result -> OutputObject

# f: (x:type) -> result
#
# dispatch by type
