"""
Base for UI generation
"""
from collections import ChainMap
from typing import Callable, Any, Union, Mapping, Iterable, TypeVar, Dict
from functools import partial
import typing

import streamlit as st

from i2 import Sig
from front.session_state import _get_state, _SessionState
from front.util import func_name

# --------------------- types/protocols/interfaces --------------------------------------

Map = Union[None, Mapping, Callable[[], Mapping]]
Configuration = Mapping
Convention = Mapping
PageFunc = Callable[[_SessionState], Any]
PageName = str
PageSpec = Mapping[PageName, PageFunc]
App = Callable
AppMaker = Callable[[Iterable[Callable], Configuration], App]


# ------- configuration/convention/default management -----------------------------------


# TODO: Lots of configs/convention/defaults stuff piling up: Needs it's own module


def func_to_page_name(func, **kwargs):
    return func_name(func).replace('_', ' ').title()


# TODO: Need to enforce SOME structure/content. Use a subclass of util.Objdict instead?
def dflt_convention():
    return dict(
        app_maker=pages_app,
        page_configs=dict(layout='wide'),
        func_to_page_name=func_to_page_name,
    )


def _get_map(mapping: Map) -> Mapping:
    """Get a concrete mapping from a flexible specification (e.g. could be a factory)"""
    if isinstance(mapping, Callable):
        return mapping()  # it's a factory, get the actual mapping
    else:
        return mapping or {}


def _get_configs(configs: Map = None, convention: Map = dflt_convention):
    configs, convention = map(_get_map, (configs, convention))  # get concrete mappings
    configs = ChainMap(configs, convention)  # merge them
    return configs


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


# def func_to_page_name(func: Callable, page_name_for_func: Map = None, **configs) -> str:
#     """Get page name for function.
#     If explicit in  page_name_for_func
#     """
#     page_name_for_func = page_name_for_func or {}
#     func_name_str = page_name_for_func.get(func, None)
#     if func_name_str is not None:
#         return func_name_str
#     else:
#         return func_name(func)

# ---------------------------------------------------------------------------------------
# The main function and raison d'etre of front


def dispatch_funcs(
    funcs: Iterable[Callable], configs: Map = None, convention: Map = dflt_convention,
) -> App:
    """Call this function with target funcs and get an app to run."""
    configs = _get_configs(configs, convention)
    app_maker = configs['app_maker']
    assert isinstance(app_maker, Callable)
    return partial(app_maker, funcs=funcs, configs=configs)


# ---------------------------------------------------------------------------------------

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
        typing.Iterable[int]: (st.number_input, int),
        typing.Iterable[float]: (st.number_input, float),
        typing.Iterable[str]: (st.number_input, str),
        typing.Iterable[bool]: (st.number_input, bool),
        typing.Dict[str, int]: (st.number_input, str, int),
        typing.Dict[str, float]: (st.number_input, str, float),
        typing.Dict[str, str]: (st.number_input, str, str),
        typing.Dict[str, bool]: (st.number_input, str, bool),
    }


P = TypeVar('P', Iterable[int], Iterable[float], Iterable[str], Iterable[bool])
K = TypeVar('K', Dict[str, int], Dict[str, float], Dict[str, str], Dict[str, bool])

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
        if inferred_type in P.__constraints__:
            element_factory = {
                'base': element_factory_for_annot.get(inferred_type, missing)[0],
                'input_type': element_factory_for_annot.get(inferred_type, missing)[1],
                'input_factory': element_factory_for_annot.get(
                    element_factory_for_annot.get(inferred_type, missing)[1], missing
                ),
            }
            factory_kwargs = {
                'label': 'Enter the number of positional arguments you would like to pass',
                'value': 0,
            }
        elif inferred_type in K.__constraints__:
            element_factory = {
                'base': element_factory_for_annot.get(inferred_type, missing)[0],
                'key_type': element_factory_for_annot.get(inferred_type, missing)[1],
                'key_factory': element_factory_for_annot.get(
                    element_factory_for_annot.get(inferred_type, missing)[1], missing
                ),
                'value_type': element_factory_for_annot.get(inferred_type, missing)[2],
                'value_factory': element_factory_for_annot.get(
                    element_factory_for_annot.get(inferred_type, missing)[2], missing
                ),
            }
            factory_kwargs = {
                'label': 'Enter the number of keyword arguments you would like to pass',
                'value': 0,
            }
        elif inferred_type is not missing:
            element_factory = element_factory_for_annot.get(inferred_type, missing)
        else:
            element_factory = dflt_element_factory

        if name in sig.defaults:
            dflt = sig.defaults[name]
            if dflt is not None:
                # TODO: type-to-element conditions must be in configs
                if isinstance(dflt, (list, tuple, set)):
                    factory_kwargs['options'] = dflt
                else:
                    factory_kwargs['value'] = dflt

        d['element_factory'] = (element_factory, factory_kwargs)

    return func_args_specs


class BasePageFunc:
    def __init__(self, func: Callable, page_title: str = '', **configs):
        self.func = func
        self.page_title = page_title
        self.configs = configs
        self.sig = Sig(func)

    def __call__(self, state):
        if self.page_title:
            st.markdown(f'''## **{self.page_title}**''')
        st.write(Sig(self.func))


class SimplePageFunc(BasePageFunc):
    def __call__(self, state):
        if self.page_title:
            st.markdown(f'''## **{self.page_title}**''')
        args_specs = get_func_args_specs(self.func)
        # func_inputs = dict(self.sig.defaults, **state['page_state'][self.func])
        func_inputs = {}
        for argname, spec in args_specs.items():
            element_factory, kwargs = spec['element_factory']
            func_inputs[argname] = element_factory(**kwargs)
        submit = st.button('Submit')
        if submit:
            st.write(self.func(**func_inputs))
            # state['page_state'][self.func].clear()


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
    func_to_page_name: Callable = func_to_page_name,
    page_factory=DFLT_PAGE_FACTORY,
    **configs,
) -> PageSpec:
    """Get pages specification dict"""
    page_names = [func_to_page_name(func, **configs) for func in funcs]
    page_callbacks = get_page_callbacks(
        funcs, page_names, page_factory=page_factory, **configs
    )
    return dict(zip(page_names, page_callbacks))


def pages_app(funcs, configs):
    state = _get_state(hash_funcs=dflt_hash_funcs)  # TODO: get from configs

    # # Experimentation -- to be reviewed if kept #############
    # if 'page_state' not in state:
    #     state['page_state'] = {}
    #     for func in funcs:
    #         state['page_state'][func] = {}
    # ######################################################

    # full page layout style
    st.set_page_config(**configs.get('page_config', {}))

    pages = get_pages_specs(funcs, **configs)

    st.sidebar.title('Navigation')
    page = st.sidebar.radio('Select your page', tuple(pages.keys()))

    # Display the selected page with the session state
    pages[page](state)

    # Mandatory to avoid rollbacks with widgets, must be called at the end of your app
    state.sync()
