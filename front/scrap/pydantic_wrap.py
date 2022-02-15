from typing import List
from streamlitfront.base import (
    BasePageFunc,
    dispatch_funcs,
)
from front.scrap.py2pydantic import func_to_pyd_input_model_cls
import streamlit as st
import streamlit_pydantic as sp
from opyrator.ui.streamlit_ui import InputUI
from opyrator import Opyrator
from pydantic import BaseModel, create_model


def pydantic_model_from_type(mytype, name='Output', field_name='result'):
    model = create_model(name, result=(mytype, ...))

    return model


class SimplePageFuncPydanticWrite(BasePageFunc):
    def __call__(self, state):
        self.prepare_view(state)
        mymodel = func_to_pyd_input_model_cls(self.func)
        name = (
            self.func.__name__
        )  # check in sig, dag, lined a better way, i2, may be displayed name: name_of_obj

        data = sp.pydantic_input(key=f'my_form_{name}', model=mymodel)

        if data:

            st.write(self.func(**data))


class SimplePageFuncPydanticWithOutput(BasePageFunc):
    def __call__(self, state):
        self.prepare_view(state)
        mymodel = func_to_pyd_input_model_cls(self.func)
        mytype = self.func.__annotations__['return']
        output_model = pydantic_model_from_type(mytype)

        name = (
            self.func.__name__
        )  # check in sig, dag, lined a better way, i2, may be displayed name: name_of_obj

        data = sp.pydantic_input(key=f'my_form_{name}', model=mymodel)

        if data:
            func_result = self.func(**data)

            instance = output_model(result=func_result)

            st.write(instance)
            sp.pydantic_output(instance)


DFLT_CONFIGS = {'page_factory': SimplePageFuncPydanticWrite}
