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
    args_str = ",".join(map(str, args))
    kwargs_str = ",".join(map(lambda kv: f"{kv[0]}={kv[1]}", kwargs.items()))
    return ",".join(filter(None, [args_str, kwargs_str]))


@wrap_kvs(data_of_obj=dill.dumps, obj_of_data=dill.loads)
class DillFiles(Files):
    """Serializes and deserializes with dill"""

    pass


def mk_mall_of_dill_stores(store_names=Iterable[StoreName], rootdir=None):
    """Make a mall of DillFiles stores"""
    rootdir = rootdir or mk_tmp_dol_dir("crude")
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
    save_name_param="save_name",
    add_store_to_func_attr="output_store",
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
            default="",
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
    mall_key_for_argname: dict = None,
    mall: Optional[Mall] = None,
    output_store: Optional[Union[Mapping, str]] = None,
    save_name_param: str = "save_name",
    include_store_for_param: bool = False,
):
    """
    Wrap func into something that is ready for CRUDE dispatch.
    It will be a function for whom specific arguments will be specified by strings,
    via underlying stores containing the values.
    We say that those arguments were crude-dispatched.

    :param func: callable, the function to wrap
    :param mall_key_for_argname: dict, whose keys specify which params should be
        crude-dispatched and whose values are the stores to be used for said param.
        Note that ``mall_key_for_argname`` can contain keys that are NOT params of ``func``.
        These will then just be ignored.
    :param output_store: a store used to record the output of the function
    :param save_name_param: str, the name used on the ui to let the user enter the name for the
    key of output_store under which the output will be saved
    :param include_store_for_param: bool, whether to add an attribute to the function containing
    the output_store

    :return:
    """

    ingress = None

    if mall_key_for_argname is not None:

        sig = Sig(func)

        store_for_param = _store_for_param(sig, mall_key_for_argname, mall)

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
                for store_name in mall_key_for_argname.values():
                    # Note: The store name is the param name.
                    # Get the argument value from outer_kw. This value is the key to
                    # the actual value we want (found in the store)
                    store_key = outer_kw[store_name]
                    # store_key points to the value the outer user wants the value for
                    # store_for_param[store_name] is the store where to find it
                    yield store_name, store_for_param[store_name][store_key]

            return dict(get_values_from_stores())

        ingress = Ingress(
            inner_sig=sig,
            kwargs_trans=kwargs_trans,
            outer_sig=(
                sig.ch_annotations(**{name: str for name in mall_key_for_argname})
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
            wrapped_f,
            store=output_store,
            save_name_param=save_name_param,
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


def _store_for_param(sig, mall_key_for_argname, mall):
    if isinstance(mall_key_for_argname, str):
        mall_key_for_argname = mall_key_for_argname.split()
    if not set(mall_key_for_argname).issubset(sig.names):
        offenders = set(mall_key_for_argname) - set(sig.names)
        raise ValueError(
            f"Some of your mall_key_for_argname keys were not argument names of "
            f"your function. These keys: {offenders}"
        )
    if not set(mall_key_for_argname.values()).issubset(mall.keys()):
        offenders = set(mall_key_for_argname.values()) - set(mall.keys())
        keys = "keys" if len(offenders) > 1 else "key"
        offenders = ", ".join(map(lambda x: f"'{x}'", offenders))

        raise ValueError(
            f"The {offenders} {keys} of your mall_key_for_argname values were not in "
            f"the mall. "
        )
    # Note: store_for_param used to be the argument of prepare_for_crude_dispatch,
    #   instead of the (mall_key_for_argname, mall) pair which is overkill.
    #   The reason for obliging the user to give this pair was because asking for
    #   the user to be more explicit about the argname to store mapping would avoid
    #   some bugs and make it possible to validate the request earlier on.
    store_for_param = {
        argname: mall[mall_key] for argname, mall_key in mall_key_for_argname.items()
    }
    return store_for_param
