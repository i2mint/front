"""
Base for UI generation
"""
import zipfile
from collections import ChainMap
from typing import Callable, Protocol, Any, Union, Optional, Mapping, Iterable, NewType
from functools import partial, wraps
from dataclasses import dataclass

import streamlit as st

from i2 import Sig
from lined import Pipe
from front.session_state import _get_state, _SessionState
from front.util import func_name

Map = Optional[Mapping]
PageFunc = Callable[[_SessionState], Any]
PageName = str
PageSpec = Mapping[PageName, PageFunc]
App = Callable


def dispatch_funcs(
    funcs: Iterable[Callable], configs: Map = None, convention: Map = None,
) -> App:
    """Call this function with target funcs and get an app to run."""
    configs = ChainMap(configs or {}, convention or {})
    return partial(pages_app, funcs=funcs, configs=configs)


# full page layout style
st.set_page_config(layout='wide')


def default_hash_func(item):
    return id(item)


class DfltDict(dict):
    def __missing__(self, k):
        return default_hash_func


dflt_hash_funcs = DfltDict(
    {
        'abc.WfStoreWrapped': default_hash_func,
        'qcoto.dacc.Dacc': default_hash_func,
        'abc.DfSimpleStoreWrapped': default_hash_func,
        'builtins.dict': default_hash_func,
    }
)


def func_to_page_name(func: Callable, page_name_for_func: Map = None, **configs) -> str:
    """Get page name for function.
    If explicit in  page_name_for_func
    """
    page_name_for_func = page_name_for_func or {}
    func_name_str = page_name_for_func.get(func, None)
    if func_name_str is not None:
        return func_name_str
    else:
        return func_name(func)


class BasePageFunc:
    def __init__(self, func: Callable, page_title: str = '', **configs):
        self.func = func
        self.page_title = page_title
        self.configs = configs

    def __call__(self, state):
        if self.page_title:
            st.markdown(f'''## **{self.page_title}**''')
        st.write(Sig(self.func))


missing = type('Missing', (), {})()


def infer_type(sig, name):
    if name in sig.annotations:
        return sig.annotations[name]
    elif name in sig.defaults:
        dflt = sig.defaults[name]
        if dflt is not None:
            return type(dflt)
    else:
        return missing


def _get_dflt_element_factory_for_annot():
    _ = _get_state()
    return {
        int: st.number_input,
        float: st.number_input,
        str: st.text_input,
        bool: st.checkbox,
        list: st.selectbox,
        type(
            lambda df: df
        ): st.file_uploader,  # TODO: Find a better way to identify as file_uploader
        type(_): None,
    }


# TODO: Too messy -- needs some design thinking
# TODO: Basic: Add some more smart mapping
def get_func_args_specs(
    func,
    dflt_element_factory=st.text_input,
    element_factory_for_annot: Mapping = None,
    **configs,
):
    element_factory_for_annot = (
        element_factory_for_annot or _get_dflt_element_factory_for_annot()
    )
    sig = Sig(func)
    func_args_specs = {name: {} for name in sig.names}
    for name in sig.names:
        d = func_args_specs[name]
        factory_kwargs = {'label': name}
        inferred_type = infer_type(sig, name)
        if inferred_type is not missing:
            element_factory = element_factory_for_annot.get(inferred_type, missing)
        else:
            element_factory = dflt_element_factory

        if name in sig.defaults:
            dflt = sig.defaults[name]
            if dflt is not None:
                if isinstance(dflt, list):
                    factory_kwargs['options'] = dflt
                else:
                    factory_kwargs['value'] = dflt

        d['element_factory'] = (element_factory, factory_kwargs)

    return func_args_specs


class SimplePageFunc(BasePageFunc):
    def __call__(self, state):
        if self.page_title:
            st.markdown(f'''## **{self.page_title}**''')
        args_specs = get_func_args_specs(self.func)
        func_inputs = {}
        for argname, spec in args_specs.items():
            element_factory, kwargs = spec['element_factory']
            func_inputs[argname] = element_factory(**kwargs)
        submit = st.button('Submit')
        if submit:
            st.write(self.func(**func_inputs))


class DataAccessPageFunc(BasePageFunc):
    def __call__(self, state):
        if self.page_title:
            st.markdown(f'''## **{self.page_title}**''')
        st.write(
            'Current value stored in state for this function is:',
            state[self.page_title],
        )
        args_specs = get_func_args_specs(self.func)
        func_inputs = {}
        for argname, spec in args_specs.items():
            if spec['element_factory'][0] is None:
                func_inputs[argname] = state
            else:
                if 'options' in spec['element_factory'][1]:
                    pass  # TODO: find some way to access the data from another input we want
                element_factory, kwargs = spec['element_factory']
                func_inputs[argname] = element_factory(**kwargs)
        submit = st.button('Submit')
        if submit:
            state[self.page_title] = self.func(**func_inputs)
            st.write(state[self.page_title])


class ScrapPageFunc(BasePageFunc):
    def __call__(self, state):
        if self.page_title:
            st.markdown(f'''## **{self.page_title}**''')
        st.write(
            'Current value stored in state for this function is:',
            state[self.page_title],
        )
        args_specs = get_func_args_specs(self.func)
        i = 0
        temp = {}
        for key in args_specs.keys():
            temp[i] = key
            i += 1
        func_inputs = {}
        for num, argname in temp.items():
            # only works under the assumptions that the first argument for every function will be to pass the state
            # and the options for the selectbox are the argument directly before it is a string of comma separated
            # values
            if num == 0:
                func_inputs[argname] = state
            else:
                if func_inputs[temp[num - 1]]:
                    if args_specs[argname]['element_factory'][0] is None:
                        func_inputs[argname] = state
                    else:
                        if 'options' in args_specs[argname]['element_factory'][1]:
                            options = func_inputs[temp[num - 1]].split(', ')
                            args_specs[argname]['element_factory'][1][
                                'options'
                            ] = options
                        element_factory, kwargs = args_specs[argname]['element_factory']
                        func_inputs[argname] = element_factory(**kwargs)
        submit = st.button('Submit')
        if submit:
            state[self.page_title] = self.func(**func_inputs)
            st.write(
                'New value stored in state for this function is:',
                state[self.page_title],
            )


DFLT_PAGE_FACTORY = ScrapPageFunc  # Try BasePageFunc too


# TODO: Code this!
def get_page_callbacks(funcs, page_names, page_factory=DFLT_PAGE_FACTORY, **configs):
    return [
        page_factory(func, page_name, **configs)
        for func, page_name in zip(funcs, page_names)
    ]


# TODO: Get func_page for real
def get_pages_specs(
    funcs: Iterable[Callable],
    func_to_page: Callable = func_to_page_name,
    page_factory=DFLT_PAGE_FACTORY,
    **configs,
) -> PageSpec:
    page_names = [func_to_page(func, **configs) for func in funcs]
    page_callbacks = get_page_callbacks(funcs, page_names, **configs)
    return {
        page_name: page_callback
        for page_name, page_callback in zip(page_names, page_callbacks)
    }


def pages_app(funcs, configs):
    state = _get_state(hash_funcs=dflt_hash_funcs)  # TODO: get from configs

    def func_to_name(func):
        name = func_name(func)
        name = name.replace('_', ' ').title()
        return name

    pages = get_pages_specs(funcs, func_to_name, **configs)

    # pages = {
    #     'Upload Dataset': page_upload,
    #     'Select Sessions and Phases': page_session,
    #     'Train Model': page_model_training,
    #     'Model Results': page_model_results,
    # }

    st.sidebar.title('Navigation')
    page = st.sidebar.radio('Select your page', tuple(pages.keys()))

    # Display the selected page with the session state
    pages[page](state)

    # Mandatory to avoid rollbacks with widgets, must be called at the end of your app
    state.sync()
