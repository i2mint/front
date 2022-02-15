"""A simple app to demo the use of Mappings to handle complex type"""
from typing import Mapping
from i2.wrapper import wrap

from enum import Enum
from typing import Set
from dataclasses import dataclass, field, make_dataclass
from typing import List
import streamlit as st
from pydantic import BaseModel, Field, ValidationError, parse_obj_as

# from front.scrap.pydantic_wrap import SimplePageFuncPydanticWrite

import streamlit_pydantic as sp
from streamlitfront.base import (
    BasePageFunc,
    dispatch_funcs,
)
from front.scrap.py2pydantic import func_to_pyd_input_model_cls

ComplexType = float  # just pretend it's complex!


def func(salary: ComplexType, n_months: int = 12) -> float:
    return salary * n_months


SalaryKey = str  # or some type that will resolve in store-fed key selector
SalaryMapping = Mapping[SalaryKey, ComplexType]

salary_store: SalaryMapping
salary_store = {'sylvain': 10000, 'christian': 2000, 'thor': 50000}


def mk_choices_from_store(store):
    choices = Enum('Choices', {key: key for key in store.keys()})
    return choices


class ChoiceModel(BaseModel):
    single_selection: mk_choices_from_store(salary_store) = Field(
        ..., description='Only select a single item from a set.'
    )


def wrapped_func(selection: ChoiceModel, n_months: int):
    selection = selection['single_selection']
    salary_val = salary_store[selection]

    return func(salary_val, n_months)


class SimplePageFuncPydanticWrite(BasePageFunc):
    def __call__(self, state):
        self.prepare_view(state)
        mymodel = func_to_pyd_input_model_cls(self.func)
        name = (
            self.func.__name__
        )  # check in sig, dag, lined a better way, i2, may be displayed name: name_of_obj

        data = sp.pydantic_form(key=f'my_form_{name}', model=mymodel)

        if data:

            st.write(self.func(**data))


configs = {'page_factory': SimplePageFuncPydanticWrite}

if __name__ == '__main__':
    from streamlitfront.base import dispatch_funcs

    app = dispatch_funcs([func, wrapped_func], configs=configs)
    app()
