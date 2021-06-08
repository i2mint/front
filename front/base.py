"""
Base for UI generation
"""
from collections import ChainMap
from typing import Callable, Protocol, Any, Union, Optional, Mapping, Iterable
from functools import partial

import streamlit as st

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


# TODO: Get func_page for real
def get_pages_specs(
    funcs: Iterable[Callable], func_to_page: Callable = func_to_page_name, **other_kwargs
) -> PageSpec:
    page_funcs = get_page_funcs(funcs)
    return {func_to_page(func, **other_kwargs): func for func in funcs}


# TODO: Code this!
def get_page_funcs(funcs, **configs):
    return [func for func in funcs]


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
