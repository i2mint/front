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
from pydantic import BaseModel


class SimplePageFuncPydantic(BasePageFunc):
    def __call__(self, state):
        self.prepare_view(state)
        mymodel = func_to_pyd_input_model_cls(self.func)
        name = (
            self.func.__name__
        )  # check in sig, dag, lined a better way, i2, may be displayed name: name_of_obj

        data = sp.pydantic_input(key=f'my_form_{name}', model=mymodel)

        if data:

            st.write(self.func(**data))


DFLT_CONFIGS = {'page_factory': SimplePageFuncPydantic}
