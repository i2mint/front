"""
Base for UI generation
"""
from collections import ChainMap
from typing import Callable, Protocol, Any, Union, Optional, Mapping, Iterable
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
    return {
        int: st.number_input,
        float: st.number_input,
        str: st.text_input,
        bool: st.checkbox,
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
                factory_kwargs['value'] = dflt

        d['element_factory'] = partial(element_factory, **factory_kwargs)

    return func_args_specs


class SimplePageFunc(BasePageFunc):
    def __call__(self, state):
        if self.page_title:
            st.markdown(f'''## **{self.page_title}**''')
        args_specs = get_func_args_specs(self.func)
        for argname, spec in args_specs.items():
            spec['element_factory']()
        # TODO: Make submit button that gathers all inputs, and calls self.func with them
        # func_inputs = ...
        # st.write(self.func(**func_inputs))


DFLT_PAGE_FACTORY = SimplePageFunc  # Try BasePageFunc too

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

    pages = get_pages_specs(funcs, **configs)

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
