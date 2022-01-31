from streamlitfront.base import (
    BasePageFunc,
    dispatch_funcs,
)
from front.scrap.py2pydantic import func_to_pyd_input_model_cls
import streamlit as st
import streamlit_pydantic as sp


class SimplePageFuncPydantic(BasePageFunc):
    def __call__(self, state):
        self.prepare_view(state)
        mymodel = func_to_pyd_input_model_cls(self.func)
        data = sp.pydantic_input(key='my_form', model=mymodel)

        if data:
            st.write(self.func(**data))


def myfunc(x: int, y: str):
    return x * y


funcs = [myfunc]
configs = {'page_factory': SimplePageFuncPydantic}


if __name__ == '__main__':
    from streamlitfront import dispatch_funcs

    app = dispatch_funcs(funcs, configs=configs)
    app()
