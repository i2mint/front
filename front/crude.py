"""
CRUDE stands for CRUD-Execution.
It is a method to solve the problem of dealing with complex python objects in an
environment that doesn't natively support these.

The method's trick is to allow the complex object's that we "crudified" to be controlled
via a string key that references the complex object, via a "store" which maps
these string keys to the actual physical object.
This store could be a python dictionary (so in RAM) or any persisting storage system
(files, DB) that is given a `typing.Mapping` interface
(see https://i2mint.github.io/dol/ or https://i2mint.github.io/py2store for
tools to do so).

Take, for instance, a GUI that allows a user to compute some descriptive statistics
of the columns of a table.
The inputs are a table, and one of the following statistics function:
``statistics.mean``, ``statistics.median``, or ``statistics.stdev``.

Python functions are not a type natively handled by GUI, so what can we do?
We can stick a layer between our ``compute_stats(stats_func, table)`` function
and our GUI, endowed with a
``{"mean": statistics.mean``, "median": statistics.median, "std": statistics.stdev}``
mapping. We expose the string keys to the GUI, and map them to the functions before
calling ``compute_stats``.

In the case of the ``table``, we'd probably add a means for the GUI user to upload
tables (say from ``.csv`` or ``.xlsx`` files), storing them under a name of their
choice, then pointing to said table via the name, when they want to execute a
``compute_stats(stats_func, table)``.

These are examples of what we call "crudifying" variables or functions.

Here we therefore offer tools to do this sort of thing;
wrap functions so that the complex arguments can be specified through a string key
that points to the actual python object (which is stored in a session's memory or
persisted in some fashion).
"""

from typing import Any, Mapping, Optional, Callable, Union, Iterable, Iterator
from inspect import Parameter
import os
from functools import partial

import dill  # pip install dill

from i2 import Sig, double_up_as_factory
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


from functools import wraps
from i2 import call_forgivingly


def _validate_function_keyword_only_params(func, allowed_params: Iterable, obj_name):
    if func is not None:
        if not callable(func):
            raise TypeError(f'{obj_name} should be callable: {func}')
        sig = Sig(func)
        if not all(kind == Parameter.KEYWORD_ONLY for kind in sig.kinds.values()):
            raise TypeError(f'All params of {obj_name} must be keyword-only. {sig}')
        if not set(sig.names).issubset(allowed_params):
            raise TypeError(f'All params of {obj_name} must be in {allowed_params}')


def _store_on_output(*args, _store_on_ouput_args, **kwargs):
    # TODO: Assuming order is dangerous. Add extra safety. E.g. extract from dict.
    (
        func,
        sig,
        store,
        save_name_param,
        empty_name_callback,
        auto_namer,
        output_trans,
    ) = _store_on_ouput_args
    arguments = sig.kwargs_from_args_and_kwargs(args, kwargs, apply_defaults=True)
    save_name = arguments.pop(save_name_param)
    if not save_name and empty_name_callback:
        assert callable(
            empty_name_callback
        ), f'empty_name_callback must be callable: {empty_name_callback}'
        empty_name_callback()
    args, kwargs = sig.args_and_kwargs_from_kwargs(arguments)
    output = func(*args, **kwargs)
    if not save_name and auto_namer:
        save_name = call_forgivingly(auto_namer, arguments=arguments, output=output)
    if save_name:
        store[save_name] = output
    if not output_trans:
        return output
    else:
        return call_forgivingly(
            output_trans, save_name=save_name, output=output, arguments=arguments
        )


# TODO: store_on_output not pickalable: extend i2.wrapper to be able to solve with it
@double_up_as_factory
def store_on_output(
    func=None,
    *,
    store=None,
    save_name_param='save_name',
    add_store_to_func_attr='output_store',
    empty_name_callback: Callable[[], Any] = None,
    auto_namer: Callable[..., str] = None,
    output_trans: Callable[..., Any] = None,
):
    """Wrap func so it will have an extra save_name_param that can be used to
    indicate whether to save the output of the function call to that key, in
    that store.

    The store can be specified, but an empty dict will be made for it by default.

    By default, a pointer to this store is added to the wrapped function so it can be
    used for inspection etc.

    :param func: Function that we're wrapping
    :param store: Mapping (e.g. dict) where we'd like the output to be stored in
    :param save_name_param: Name of the extra param that will be added to the
        function's interface, where the user will be able to specify the key where
        they want to save the output.
    :param add_store_to_func_attr: If not None, the wrapped function will have an
        attribute of that name where the store will be stored
    :param empty_name_callback: If not None, will be called if the user doesn't specify
        a save name. Intended use; raising errors to force the user to enter name.
    :param auto_namer: If not None, should be a keyword-only ``(*, arguments, output)``
        callback that will be called (forgivingly). This callback will
        be called when the user doesn't specify a name (or an empty name). It's output
        will be used as the ``save_name``.
    :param output_trans: If not None, should be a keyword-only
        ``(*, save_name, output, arguments)`` function that will be called, returning
        it's result instead of the ``output``.
    :return: A wrapped function that has an extra param (default is ``save_name``) that
        allowing the user to specify a key under which to save the output.

    A simple example:

    >>> def foo(a, b: int = 2):
    ...     return a + b
    >>> f = store_on_output(foo)
    >>> f(2, 3, save_name='take')
    5
    >>> f.output_store
    {'take': 5}

    An example with auto_namer. Note that an auto_namer can have no parameters (e.g.
    return a stringified timestamp for the auto-name), but if it does have any
    parameters, these parameters must be keyword-only and the only names allowed are:

    - ``save_name``, which will contain the value of the name the user entered

    - ``output``, which will contain the return value of the function call

    - ``arguments``, which will contain a dict of all the arguments of the function call

    In the following, we will make an ``output_trans`` that just returns the
    ``save_name``. This is useful when you want to make a pipeline and tell the next
    function where to find the output of a previous function.

    >>> def return_key(*, save_name):
    ...     return save_name
    >>> g = store_on_output(foo, output_trans=return_key)
    >>> g(100, 23, save_name='test')
    'test'
    >>> g.output_store
    {'test': 123}
    >>> g.output_store[g(40, 2, save_name='here')]
    42

    An example involving more params:

    >>> my_store = {'all': 'mine'}
    >>> @store_on_output(
    ...     store=my_store,
    ...     save_name_param='save_as',
    ...     add_store_to_func_attr=None,
    ...     auto_namer=lambda *, arguments: '_'.join(map(str, arguments.values()))
    ... )
    ... def bar(a, b: int = 2):
    ...     return a + b
    >>> bar(2, 3, save_as='test')
    5
    >>> my_store
    {'all': 'mine', 'test': 5}
    >>> bar(7)
    9
    >>> my_store
    {'all': 'mine', 'test': 5, '7_2': 9}

    """
    save_name_param_obj = Parameter(
        name=save_name_param, kind=Parameter.KEYWORD_ONLY, default='', annotation=str,
    )
    _validate_function_keyword_only_params(
        auto_namer, ['output', 'arguments'], obj_name='auto_namer'
    )
    _validate_function_keyword_only_params(
        output_trans, ['save_name', 'output', 'arguments'], obj_name='output_trans'
    )
    if output_trans:
        assert callable(output_trans) and set(Sig(output_trans).names).issubset(
            ['save_name', 'output', 'arguments']
        )
    sig = Sig(func) + [save_name_param_obj]

    if store is None:
        store = dict()

    __func = partial(
        _store_on_output,
        _store_on_ouput_args=(
            func,
            sig,
            store,
            save_name_param,
            empty_name_callback,
            auto_namer,
            output_trans,
        ),
    )

    new_return_annotation = (
        Sig(output_trans).return_annotation if output_trans else Parameter.empty
    )
    if new_return_annotation != Parameter.empty:
        sig = sig.replace(return_annotation=new_return_annotation)

    _func = sig(wraps(func)(__func))

    if isinstance(add_store_to_func_attr, str):
        setattr(_func, add_store_to_func_attr, store)

    return _func


@double_up_as_factory
def prepare_for_crude_dispatch(
    func: Callable = None,
    *,
    param_to_mall_map: Optional[Union[dict, Iterable]] = None,
    mall: Optional[Mall] = None,
    include_stores_attribute: bool = False,
    output_store: Optional[Union[Mapping, str]] = None,
    # the arguments below only apply if output_store is given
    save_name_param: str = 'save_name',
    empty_name_callback: Callable[[], Any] = None,
    auto_namer: Callable[..., str] = None,
    output_trans: Callable[..., Any] = None,
):
    """
    Wrap func into something that is ready for CRUDE dispatch.
    It will be a function for whom specific arguments will be specified by strings,
    via underlying stores containing the values.
    We say that those arguments were crude-dispatched.

    :param func: callable, the function to wrap
    :param param_to_mall_map: dict, whose keys specify which params should be
        crude-dispatched and whose values are the mall keys to the Mapping instances
        (e.g. dict) that should be used for said param.
        If a non-Mapping iterable is given, will take {name: name...} identity mapping
        for names in that iterable.
    :param mall: A store of stores. A Mapping whose keys are what the values of
        ``param_to_mall_map`` point to and whose values are mapping interfaces (called
         "stores" of a storage backend (local or remote, persisted or in-memory).
    :param include_stores_attribute: bool, whether to add an attribute to the function
        containing the ``output_store``
    :param output_store: a store used to record the output of the function

    If (and only if) ``output_store`` is given, we can also use the following
    arguments to control the output "crudification" further.

    :param save_name_param: str, the argument name that should be used in the returned
        functions to get the the key of ``output_store`` under which the output will be
        saved.
    :param empty_name_callback: If not None, will be called when the user (of the
        wrapped function ``prepare_for_crude_dispatch`` will output) doesn't
        specify a save name. Intended use; raising errors (or other kinds of behavior)
        when we want to force the user to enter name.
    :param auto_namer: If not None, should be a keyword-only ``(*, arguments, output)``
        callback that will be called (forgivingly). This callback will
        be called when the user doesn't specify a name (or an empty name). It's output
        will be used as the ``save_name``. Intended use is to produce a function where
        that has auto-naming capabilities.
    :param output_trans: If not None, should be a keyword-only
        ``(*, save_name, output, arguments)`` function that will be called, returning
        it's result instead of the ``output``.

    :return: A function that outputs the same thing as ``func``, but (1) with some
        parameters being changed so that on can specify some arguments
        (those listed by ``param_to_mall_key_dict``)


    >>> def func(a, b: float, c: int):
    ...     return a + b * c
    ...
    >>> param_to_mall_map = dict(a='a', b='b_store')
    >>>
    >>> mall = dict(
    ...     a = {'one': 1, 'two': 2},
    ...     b_store = {'three': 3, 'four': 4},
    ...     unused_store = {'to': 'illustrate'}
    ... )
    >>> crude_func = prepare_for_crude_dispatch(
    ...     func, param_to_mall_map=param_to_mall_map, mall=mall
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

    By default, the ``output_store`` argument is None, but if you specify a mapping
    there (or a string key that appears in the ``mall`` you specified, pointing to
    a mapping), then the function you'll get will have an extra argument.

    >>> output_store = dict()
    >>> crude_func = prepare_for_crude_dispatch(
    ...     func,
    ...     param_to_mall_map=param_to_mall_map,
    ...     mall=mall,
    ...     output_store=output_store
    ... )
    >>> str(signature(crude_func))
    "(a: str, b: str, c: int, save_name: str = '')"

    You now have this extra ``save_name`` param in your function.
    (Note that you can change its name through the ``prepare_for_crude_dispatch``'s
    ``save_name_param`` argument.)
    The default for ``save_name`` is '', and if you don't specify a non-empty
    string, nothing different will happen, but if you do specify a non-empty string,
    the output of your function will be saved, in the ``output_store`` you specified,
    using that ``save_name`` key you specified.

    >>> crude_func('one', 'three', 10)
    31
    >>> output_store
    {}
    >>> crude_func('one', 'three', 10, save_name='save_here')
    31
    >>> output_store
    {'save_here': 31}

    The example below shows how one can

    - change the default ``save_name_param``

    - use an ``auto_namer``

    - use ``output_trans`` to return both save name and output

    >>> def bar(a, b: int = 2):
    ...     return a + b
    >>> my_store = {'all': 'mine'}
    >>> def return_key_and_val(*, save_name, output):
    ...     return save_name, output
    >>> wbar = prepare_for_crude_dispatch(
    ...     bar,
    ...     output_store=my_store,
    ...     save_name_param='save_as',
    ...     auto_namer=lambda *, arguments: '_'.join(map(str, arguments.values())),
    ...     output_trans=return_key_and_val
    ... )

    >>> wbar(2, 3, save_as='test')  # output will be the (save_as, output) pair
    ('test', 5)
    >>> my_store  # but only the output is saved (under save_as key)
    {'all': 'mine', 'test': 5}
    >>> wbar(7)  # and if you don't specify a save_as key, one is made for you!
    ('7_2', 9)
    >>> my_store
    {'all': 'mine', 'test': 5, '7_2': 9}
    """
    ingress = None

    store_for_param = {}

    if param_to_mall_map is not None:

        sig = Sig(func)

        # get an {argname: store, ...} dict from param_to_mall_map:
        store_for_param = _mk_store_for_param(sig, param_to_mall_map, mall) or dict()

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
                sig.ch_annotations(**{name: str for name in store_for_param})
                # + [save_name_param]
            ),
        )

    wrapped_f = wrap(func, ingress=ingress)

    if include_stores_attribute:
        wrapped_f.store_for_param = store_for_param

    if output_store is not None:
        output_store_name = 'output_store'
        if isinstance(output_store, str):
            # if output_store is a string, it should be the a key to store_for_param
            output_store_name = output_store
            output_store = mall[output_store_name]
        else:
            # TODO: Assert MutableMapping, or just existence of __setitem__?
            if not hasattr(output_store, '__setitem__'):
                raise ValueError(f'Needs to have a __setitem__: {output_store}')
        if output_store_name in store_for_param:
            raise ValueError(
                f'Name conflicts with existing param name: {output_store_name}'
            )

        wrapped_f = store_on_output(
            wrapped_f,
            store=output_store,
            save_name_param=save_name_param,
            add_store_to_func_attr='output_store' if include_stores_attribute else None,
            empty_name_callback=empty_name_callback,
            auto_namer=auto_namer,
            output_trans=output_trans,
        )
        # wrapped_f.__name__ = wrapped_f.__name__ + "_w_output_storing"  # to remove

    return wrapped_f


def _mk_store_for_param(sig, param_to_mall_key_dict=None, mall=None, verbose=True):
    """Make a {param: store,...} dict from a {param: mall_key,...} dict, a sig and a
    mall, validating stuff on the way."""
    mall = mall or dict()
    param_to_mall_key_dict = keys_to_values_if_non_mapping_iterable(
        param_to_mall_key_dict
    )
    # mall_keys_that_are_also_params_but_not_param_to_mall_key_dict_keys
    unmentioned_mall_keys = set(mall) & set(sig.names) - set(param_to_mall_key_dict)
    if unmentioned_mall_keys and verbose:
        from warnings import warn

        warn(
            f"Some of your mall keys were also func arg names, but you didn't mention "
            f'them in param_to_mall_map, namely, these: {unmentioned_mall_keys}'
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
                'The param_to_mall_map should only contain keys that are '
                f"parameters (i.e. 'argument names') of your function {func_name_stub}. "
                f'Yet these param_to_mall_map keys were not argument names: '
                f'{offenders}'
            )
        if not set(param_to_mall_key_dict.values()).issubset(mall.keys()):
            offenders = set(param_to_mall_key_dict.values()) - set(mall.keys())
            keys = 'keys' if len(offenders) > 1 else 'key'
            offenders = ', '.join(map(lambda x: f"'{x}'", offenders))

            raise ValueError(
                f'The {offenders} {keys} of your param_to_mall_map values were not '
                f'in the mall. Your param_to_mall_key_dict is:\n'
                f'{param_to_mall_key_dict} and your mall has keys: {list(mall)}. '
                f'You can either add {offenders} stores to the mall, '
                # f'make an auto-store-making mall (e.g. collections.defaultdict(dict), '
                f'or change your param_to_mall_map to point (values) to a store that '
                f'you actually have in the mall'
            )
        # Note: store_for_param used to be the argument of prepare_for_crude_dispatch,
        #   instead of the (param_to_mall_map, mall) pair which is overkill.
        #   The reason for obliging the user to give this pair was because asking for
        #   the user to be more explicit about the argname to store mapping would avoid
        #   some bugs and make it possible to validate the request earlier on.
        store_for_param = {
            argname: mall[mall_key]
            for argname, mall_key in param_to_mall_key_dict.items()
        }
        return store_for_param


def keys_to_values_if_non_mapping_iterable(d: Optional[Iterable]) -> dict:
    if d is None:
        return dict()
    elif not isinstance(d, Mapping) and isinstance(d, Iterable):
        d = {k: k for k in d}
    return d


# Note: This is not meant to actually be used in real apps, but be a drop in helper to
#   talk to the mall (or rather "listen" since it's read-only) from a UI.
def simple_mall_dispatch_core_func(
    key: KT, action: str, store_name: StoreName, mall: Mall
):
    """Helper function to dispatch a mall

    This function is only meant to be a helper to give a UI (GUI,
    CLI...) mall-exploration capabilities. Namely:

    - ``list(mall)``: list the keys of a mall. This is achieved with args:
        ``(key=None, action=None, store_name=None, mall=mall)``
    - ``mall[store_name]``: get a store. Acheived by:
        ``(key=None, action=None, store_name=store_name, mall=mall)``
    - ``list(mall[store_name])``: list keys of a store (of the mall). Acheived by:
        ``(key=None, action='list', store_name=store_name, mall=mall)``
    - ``list(filter(key, mall[store_name]))``: list keys of a store (of the mall)
        according to a substring filter. (only keys that have ``key`` as substring)
        ``(key=key, action='list', store_name=store_name, mall=mall)``
    - ``mall[store_name][key]``:  get the value/data of a store for ``key``
        ``(key=key, action='get', store_name=store_name, mall=mall)``

    :param key: The key
    :param action: 'list' (to list keys of a store) or 'get' (to get the value of
        ``key`` in the store (named ``store_name``)
    :param store_name: Store name to look up in mall. If not given, the function will
        output the mall keys (which are valid store names)
    :param mall: dict of stores (Mapping interface to data)
    :return:

    >>> mall = {
    ...     'english': {'one': 1, 'two': 2, 'three': 3},
    ...     'french': {'un': 1, 'deux': 2},
    ... }

    List the keys of a mall:

    >>> simple_mall_dispatch_core_func(None, None, None, mall=mall)
    ['english', 'french']

    Get a store

    >>> simple_mall_dispatch_core_func(None, None, store_name='english', mall=mall)
    {'one': 1, 'two': 2, 'three': 3}

    List keys of a store (of the mall):

    >>> simple_mall_dispatch_core_func(
    ...     None, action='list', store_name='english', mall=mall
    ... )
    ['one', 'two', 'three']

    List keys of a store (of the mall) according to a substring filter:

    >>> simple_mall_dispatch_core_func(
    ...     'e', action='list', store_name='english', mall=mall
    ... )
    ['one', 'three']

    >>> simple_mall_dispatch_core_func(
    ...     'two', action='get', store_name='english', mall=mall
    ... )
    2


    """
    if not store_name:
        # if store_name empty, list the store names (i.e. the mall keys)
        return list(mall)
    else:  # if not, get the store
        store = mall[store_name]
        if not action:
            return store

    key = key or ''
    if action == 'list':
        key = key.strip()  # to handle some invisible whitespace that would screw things
        return list(filter(lambda k: key in k, store))
    elif action == 'get':
        return store[key]
