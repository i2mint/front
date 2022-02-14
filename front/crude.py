"""
Control complex python object through strings.
Wrap functions so that the complex arguments can be specified through a string key
that points to the actual python object (which is stored in a session's memory or
persisted in some fashion).
"""

from typing import Any, Mapping, Optional, Callable, Union, Iterable
from functools import partial
from inspect import Parameter
import os

import dill  # pip install dill

from i2 import Sig
from i2.wrapper import Ingress, wrap
from dol import Files, wrap_kvs
from dol.filesys import mk_tmp_dol_dir, ensure_dir


KT = str
VT = Any
StoreType = Mapping[KT, VT]
StoreName = KT
Mall = Mapping[StoreName, StoreType]


def auto_key(*args, **kwargs) -> KT:
    """Make a str key from arguments.

    >>> auto_key(1,2,c=3,d=4)
    '1,2,c=3,d=4'
    >>> auto_key(1,2)
    '1,2'
    >>> auto_key(c=3,d=4)
    'c=3,d=4'
    >>> auto_key()
    ''
    """
    args_str = ','.join(map(str, args))
    kwargs_str = ','.join(map(lambda kv: f'{kv[0]}={kv[1]}', kwargs.items()))
    return ','.join(filter(None, [args_str, kwargs_str]))


@wrap_kvs(data_of_obj=dill.dumps, obj_of_data=dill.loads)
class DillFiles(Files):
    """Serializes and deserializes with dill"""

    pass


def mk_mall_of_dill_stores(store_names=Iterable[StoreName], rootdir=None):
    """Make a mall of DillFiles stores"""
    rootdir = rootdir or mk_tmp_dol_dir('crude')
    if isinstance(store_names, str):
        store_names = store_names.split()

    def name_and_rootdir():
        for name in store_names:
            root = os.path.join(rootdir, name)
            ensure_dir(root)
            yield name, root

    return {name: DillFiles(root) for name, root in name_and_rootdir()}


# TODO: store_on_output: use i2.wrapper and possibly extend i2.wrapper to facilitate
from functools import wraps


def store_on_output(
    func=None,
    *,
    store=None,
    save_name_param='save_name',
    add_store_to_func_attr='output_store',
):
    """Wrap func so it will have an extra save_name_param that can be used to
    indicate whether to save the output of the function call to that key, in
    that store

    :param func:
    :param store:
    :param save_name_param: Name of the extra param
    :return:
    """
    if func is None:
        return partial(
            store_on_output,
            store=store,
            save_name_param=save_name_param,
            add_store_to_func_attr=add_store_to_func_attr,
        )
    else:
        save_name_param_obj = Parameter(
            name=save_name_param,
            kind=Parameter.KEYWORD_ONLY,
            default='',
            annotation=str,
        )
        sig = Sig(func) + [save_name_param_obj]

        if store is None:
            store = dict()

        @sig
        @wraps(func)
        def _func(*args, **kwargs):
            kwargs = sig.kwargs_from_args_and_kwargs(args, kwargs, apply_defaults=True)
            save_name = kwargs.pop(save_name_param)
            args, kwargs = sig.args_and_kwargs_from_kwargs(kwargs)
            output = func(*args, **kwargs)
            if save_name:
                store[save_name] = output
            return output

        if isinstance(add_store_to_func_attr, str):
            setattr(_func, add_store_to_func_attr, store)

        # _func.output_store = store  # redundant with above. Remove

        return _func


def prepare_for_crude_dispatch(
    func: Callable,
    param_to_mall_key_dict: Optional[Iterable] = None,
    *,
    mall: Optional[Mall] = None,
    output_store: Optional[Union[Mapping, str]] = None,
    save_name_param: str = 'save_name',
    include_store_for_param: bool = False,
):
    """
    Wrap func into something that is ready for CRUDE dispatch.
    It will be a function for whom specific arguments will be specified by strings,
    via underlying stores containing the values.
    We say that those arguments were crude-dispatched.

    :param func: callable, the function to wrap
    :param param_to_mall_key_dict: dict, whose keys specify which params should be
        crude-dispatched and whose values are the mall keys to the Mapping instances
        (e.g. dict) that should be used for said param.
    :param output_store: a store used to record the output of the function
    :param save_name_param: str, the argument name that should be used in the returned
        functions to get the the key of ``output_store`` under which the output will be
        saved.
    :param include_store_for_param: bool, whether to add an attribute to the function
        containing the ``output_store``

    :return: A function that outputs the same thing as ``func``, but (1) with some
        parameters being changed so that on can specify some arguments
        (those listed by ``param_to_mall_key_dict``)


    >>> def func(a, b: float, c: int):
    ...     return a + b * c
    ...
    >>> param_to_mall_key_dict = dict(a='a', b='b_store')
    >>>
    >>> mall = dict(
    ...     a = {'one': 1, 'two': 2},
    ...     b_store = {'three': 3, 'four': 4},
    ...     ununsed_store = {'to': 'illustrate'}
    ... )
    >>> crude_func = prepare_for_crude_dispatch(
    ...     func,
    ...     param_to_mall_key_dict=param_to_mall_key_dict,
    ...     mall=mall
    ... )

    ``crude_func`` is like ``func``, but you enter your ``a`` and ``b`` inputs
    via string keys that will look up the values you're pointing to in ``mall``

    >>> assert crude_func('one', 'three', 10) == func(1, 3, 10) == 31
    >>> crude_func('one', 'three', 10)
    31
    >>> func(1, 3, 10)
    31

    What's happening behind the scenes of ``crude_func`` is this.
    Let's follow what happens for the ``b`` argument. Say the user says ``b='three'``...

    - ``b`` is a key of ``param_to_mall_key_dict``, indicating that it should be "cruded"

    - ``param_to_mall_key_dict['b']`` is ``'b_store'``, so we know which mall key to use

    - We retrieve ``mall['b_store']['three']``, which is ``3``, and call ``func`` with it

    So this is equivalent to this:

    >>> func(mall['a']['one'], mall['b_store']['three'], 10)
    31

    The signature of ``a`` and ``b`` also changed to be `str`:

    >>> from inspect import signature
    >>> str(signature(crude_func))
    '(a: str, b: str, c: int)'

    """

    ingress = None

    if param_to_mall_key_dict is not None:

        sig = Sig(func)

        store_for_param = _store_for_param(sig, param_to_mall_key_dict, mall)

        def kwargs_trans(outer_kw):
            """
            Let's say you have a function with three params: a, b, and c, whose arguments
            should be ints. Let's say you want a and c to be cruded.
            Then you need to specify a store for each one of these:

            >>> store_for_param = {
            ...     'a': {'one': 1, 'two': 2},
            ...     'c': {'three': 3}
            ... }

            What kwargs_trans will with this store_for_param, is this:

            >>> kwargs_trans({'a': 'one', 'b': 2, 'c': 'three'})
            {'a': 1, 'b': 2, 'c': 3}
            """
            # outer_kw is going to be the new/wrapped/cruded interface of the function
            # That is, the one that takes strings to specify arguments
            # What we need to do now is transform the cruded argument values from strings
            # to the values these strings are pointing to (via the store corresponding
            # to that argument).
            def get_values_from_stores():
                # Note: only need to specify arguments that change
                for param, store in store_for_param.items():
                    # param's argument value is assumed to be a store_key
                    store_key = outer_kw[param]
                    # store_key points to the value the outer user wants the value for:
                    # store is the store where to find it
                    yield param, store[store_key]

            return dict(get_values_from_stores())

        ingress = Ingress(
            inner_sig=sig,
            kwargs_trans=kwargs_trans,
            outer_sig=(
                sig.ch_annotations(**{name: str for name in param_to_mall_key_dict})
                # + [save_name_param]
            ),
        )

    wrapped_f = wrap(func, ingress)

    if output_store:
        if isinstance(output_store, str):
            # if output_store is a string, it should be the a key to store_for_param
            store_for_param_key_for_output_store = output_store
            output_store = mall[store_for_param_key_for_output_store]
        else:
            # TODO: Assert MutableMapping, or just existence of __setitem__?
            pass

        return store_on_output(
            wrapped_f, store=output_store, save_name_param=save_name_param,
        )

        # def egress(func_output):
        #     print(f"{list(store_for_param)=}")
        #     print(f"{output_store_name=}")
        #     print(f"{list(store_for_param[output_store_name])=}")
        #     store_for_param[output_store_name] = func_output
        #     print(f"{list(store_for_param[output_store_name])=}")
        #     return func_output
    if include_store_for_param:
        wrapped_f.store_for_param = store_for_param

    return wrapped_f


def _store_for_param(sig, param_to_mall_key_dict=None, mall=None, verbose=True):
    param_to_mall_key_dict = param_to_mall_key_dict or dict()
    mall = mall or dict()
    if not isinstance(param_to_mall_key_dict, Mapping) and isinstance(
        param_to_mall_key_dict, Iterable
    ):
        param_to_mall_key_dict = {k: k for k in param_to_mall_key_dict}
    # mall_keys_that_are_also_params_but_not_param_to_mall_key_dict_keys
    unmentioned_mall_keys = set(mall) & set(sig.names) - set(param_to_mall_key_dict)
    if unmentioned_mall_keys and verbose:
        from warnings import warn

        warn(
            f"Some of your mall keys were also func arg names, but you didn't mention "
            f'them in param_to_mall_key_dict, namely, these: {unmentioned_mall_keys}'
        )
    if param_to_mall_key_dict:
        func_name_stub = ''
        if sig.name:
            func_name_stub = f'({sig.name})'
        if isinstance(param_to_mall_key_dict, str):
            param_to_mall_key_dict = param_to_mall_key_dict.split()
        if not set(param_to_mall_key_dict).issubset(sig.names):
            offenders = set(param_to_mall_key_dict) - set(sig.names)
            raise ValueError(
                'The param_to_mall_key_dict should only contain keys that are '
                f"parameters (i.e. 'argument names') of your function {func_name_stub}. "
                f'Yet these param_to_mall_key_dict keys were not argument names: '
                f'{offenders}'
            )
        if not set(param_to_mall_key_dict.values()).issubset(mall.keys()):
            offenders = set(param_to_mall_key_dict.values()) - set(mall.keys())
            keys = 'keys' if len(offenders) > 1 else 'key'
            offenders = ', '.join(map(lambda x: f"'{x}'", offenders))

            raise ValueError(
                f'The {offenders} {keys} of your param_to_mall_key_dict values were not '
                f'in the mall. '
            )
        # Note: store_for_param used to be the argument of prepare_for_crude_dispatch,
        #   instead of the (param_to_mall_key_dict, mall) pair which is overkill.
        #   The reason for obliging the user to give this pair was because asking for
        #   the user to be more explicit about the argname to store mapping would avoid
        #   some bugs and make it possible to validate the request earlier on.
        store_for_param = {
            argname: mall[mall_key]
            for argname, mall_key in param_to_mall_key_dict.items()
        }
        return store_for_param
