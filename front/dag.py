"""Tools to dispatch dags

See below one of the dags that will often be used in this module's doctests:

>>> from meshed.makers import code_to_dag
>>> @code_to_dag
... def dag():
...     x = foo(a, b)
...     y = bar(x, greeting)
...     z = confuser(a, w=x)  # note the w=x to test non-trivial binding
>>> print(dag.dot_digraph_ascii())  # doctest: +SKIP

.. code-block::
     ┌──────────┐
  ┌▶ │ confuser │ ◀──    a
  │  └──────────┘
  │    │                │
  │    │                │
  │    ▼                ▼
  │                   ┌─────┐
  │       z           │ foo │ ◀──  b
  │                   └─────┘
  │                     │
  │                     │
  │                     ▼
  │
  └──────────────────    x

                        │
                        │
                        ▼
                      ┌─────┐
       greeting   ──▶ │ bar │
                      └─────┘
                        │
                        │
                        ▼

                         y



"""
from collections import defaultdict
from typing import Union, Iterable, Mapping, Any
from functools import partial
from itertools import chain

from operator import itemgetter
from enum import Enum
from dol import groupby
from front.crude import prepare_for_crude_dispatch

from meshed import DAG, FuncNode
from meshed.base import ch_func_node_attrs
from meshed.itools import parents, children


def simple_namer(name, *, prefix='', suffix=''):
    return f'{prefix}{name}{suffix}'


def crudify_func_nodes(
    var_nodes: Union[str, Iterable[str]],
    dag: DAG,
    var_node_name_to_store_name=partial(simple_namer, suffix='_store'),
    *,
    mall: Union[Mapping[str, Mapping[str, Any]], None] = None,
    include_stores_attribute: bool = False,
    save_name_param: str = 'save_name',
):
    """Crudifies the given ``var_nodes`` in the ``dag``.

    Crudifying a var node means crudifying it's ``FuncNode`` neighbors,
    i.e. telling the function that outputs to the ``VarNode`` (if any) to save it's
    output in a store and (additionally) return the key it saved it too instead of the
    value itself, and telling any consumers of the var node to use that key as it's
    argument instead, retrieving the value from said store.

    >>> from meshed import DAG, FuncNode
    >>> from inspect import signature
    >>> def foo(a, b):  return a + b
    >>> def bar(x, y):  return  x * y
    >>> dag = DAG([
    ...     FuncNode(foo, name='foo', out='foo_output'),
    ...     FuncNode(bar, bind={'y': 'foo_output'})
    ... ])

    Let's crudify ``'foo_output'``. We don't need to specify a mall, since
    ``crudify_func_nodes`` will make one for us.
    But in order to get access to it, to see what the function is doing, let's define
    a mall with a single store (a dictionary), named ``'foo_output_store'``
    (note that the map between ``var_node`` string name and
    store name is controlled by the ``var_node_name_to_store_name`` argument)

    >>> store = dict()
    >>> mall = {'foo_output_store': store}
    >>> new_dag = crudify_func_nodes(['foo_output'], dag, mall=mall)

    The ``new_dag`` is the same in structure, signature, and global behavior (you
    get the same outputs for the same inputs):

    >>> print(dag.synopsis_string())
    a,b -> foo -> foo_output
    foo_output,x -> bar_ -> bar
    >>> assert dag.synopsis_string() == new_dag.synopsis_string()
    >>> assert str(signature(dag)) == str(signature(new_dag)) == '(a, b, x)'
    >>> assert dag(2, 3, 4) == new_dag(2, 3, 4) == 20

    But let's have a closer look at the functions that ``dag`` and ``new_dag`` are
    using. The functions of the ``dag`` are the original functions we specified,
    behaving normally:

    >>> dag.func_nodes[0].func(2, 3)
    5
    >>> dag.func_nodes[1].func(4, 5)
    20

    But the first function of ``new_dag`` outputs ``'bar_last_output'`` instead of ``5``.

    >>> new_dag.func_nodes[0].func(2, 3)
    'bar_last_output'

    Where did the ``5`` go? In the mall!
    >>> mall
    {'foo_output_store': {'bar_last_output': 5}}

    So that ``5`` has been stored under the ``'bar_last_output'`` key.
    Further, the second function's second argument will no longer work with numbers,
    but with string keys, and use that same store to retrieve the value it needs for
    the underlying function:

    >>> new_dag.func_nodes[1].func(4, 'bar_last_output')
    20


    :param var_nodes: The ``VarNodes`` we want to crudify
    :param dag: The dag that contains these var_nodes
    :param var_node_name_to_store_name: The function to use to make a store for a given
        var_node name. If you have an explicit mapping ``m`` for this, just use ``m.get``
    :param mall: A ``mall`` (store of stores, i.e. mapping of mappings) whose keys are
        store names, and values are the actual stores.
    :param include_stores_attribute: Whether the crudified functions should have an
        attribute containing a pointer to the stores involved
    :param save_name_param: The name that the "save as" parameter should appear as.
    :return:
    """
    return DAG(
        list(
            _crudified_func_nodes(
                var_nodes,
                dag,
                var_node_name_to_store_name,
                mall=mall,
                include_stores_attribute=include_stores_attribute,
                save_name_param=save_name_param,
            )
        )
    )


class VarNodeRole(Enum):
    """(Var)Node roles.

    When a ``VarNode`` is used to source the arguments of a ``FuncNode``, it's playing
    a ``VarNodeRole.argument`` role.

    When a ``VarNode`` is used to store the return value of a ``FuncNode``, it's playing
    a ``VarNodeRole.return_value`` role.

    Most ``VarNode``s play both roles during a ``DAG`` computation.

    """

    argument = 'argument'
    return_value = 'return_value'


def _get_returned_by_func_node(var_node: str, dag: DAG):
    returned_by_func_node = parents(dag.graph, var_node)
    if len(returned_by_func_node) > 1:
        raise ValueError(
            f"This var_node had more than one parent. That is shouldn't be possible: "
            f'{var_node}'
        )
    return next(
        iter(returned_by_func_node), None
    )  # If None, it means it is NOT produced by a FuncNode, so is a root (input) node.


def _validate_is_func_node(node, var_node, relationship):
    if not isinstance(node, FuncNode):
        raise ValueError(f'{relationship} ({node}) of {var_node=} must be a FuncNode')


def _node_replacements_for_var_node_crudification(var_node: str, dag: DAG):
    """Helper function that generates the (node_id, (VarNodeRole, var_node)) instructions
    needed to crudify the input ``var_node`` in ``dag``.

    In the ``dag`` below, the ``var_node`` named ``x`` is the output of ``foo``
    and is used for the input of both ``bar`` (bound to the parameter of the same name)
    and ``confuser`` (bound to the ``w`` parameter).

    Therefore, as we "crudify" ``x`` we'll need to take care of all three cases:
    We'll need to have ``foo`` crudify it's output and both ``bar`` and ``confuser``
    crudify one of their params.

    >>> from meshed.makers import code_to_dag
    >>> @code_to_dag
    ... def dag():
    ...     x = foo(a, b)
    ...     y = bar(x, greeting)
    ...     z = confuser(a, w=x)  # note the w=x to test non-trivial binding
    >>> assert sorted(
    ...     _node_replacements_for_var_node_crudification('x', dag)
    ... ) == (
    ... [
    ...     ('bar', (VarNodeRole.argument, 'x')),
    ...     ('confuser', (VarNodeRole.argument, 'x')),
    ...     ('foo', (VarNodeRole.return_value, 'x')),
    ... ])

    """
    if not var_node in dag.var_nodes:
        raise ValueError(f"The {dag.name} dag doesn't have this var_node: {var_node}")

    returned_by_func_node = _get_returned_by_func_node(var_node, dag)
    if returned_by_func_node is not None:
        # If var_node is the output of a FuncNode
        # ... make sure it is.
        _validate_is_func_node(returned_by_func_node, var_node, 'Parent')
        # yield a (func_node_name, 'return_value', var_node) triple
        yield returned_by_func_node.name, (VarNodeRole.return_value, var_node)
    # if returned_by_func_node is None, skip the above: var_node is a "root" node

    # arg_of_func_nodes
    for arg_of_func_node in children(dag.graph, var_node):
        _validate_is_func_node(arg_of_func_node, var_node, 'Child')
        yield arg_of_func_node.name, (VarNodeRole.argument, var_node)


_no_more_elements = type('NoMoreElements', (), {})()


def _get_first_if_any_and_asserting_unique(
    iterable: Iterable,
    default=_no_more_elements,
    msg='Your iterator should have no more than one element',
):
    iterator = iter(iterable)
    first_element = next(iterator, default)
    assert next(iterator, _no_more_elements) == _no_more_elements, msg
    return first_element


def group_kvs_into_dict(kvs):
    return groupby(kvs, key=itemgetter(0), val=itemgetter(1))


# TODO: Skipping doctest because order not stable. Make it so
# TODO: Perhaps we should use FuncNode.name (id) instead of FuncNode itself as key of
#   dag.graph. We'd have less such problems then.
def _func_nodes_arg_and_return_names_to_crude(
    var_nodes: Union[str, Iterable[str]], dag: DAG,
):
    """Return a copy of a dag where ``var_nodes`` were crudified.

    >>> from meshed import DAG
    >>> from meshed.makers import code_to_dag
    >>> @code_to_dag
    ... def dag():
    ...     x = foo(a, b)
    ...     y = bar(x, greeting)
    ...     z = confuser(a, w=x)  # note the w=x to test non-trivial binding
    >>>
    >>> # Showing but skipping (because I can't get order to be stable (TODO: Make it so)
    >>> sorted(
    ... _func_nodes_arg_and_return_names_to_crude(['x', 'a'], dag)
    ... )  # doctest: +SKIP
    [
        (FuncNode(a,x -> confuser -> z), ('x', 'a'), None),
        (FuncNode(x,greeting -> bar -> y), ('x',), None),
        (FuncNode(a,b -> foo -> x), ('a',), 'x')
    ]

    """
    if isinstance(var_nodes, str):
        var_nodes = var_nodes.split()

    get_node_replacements = partial(
        _node_replacements_for_var_node_crudification, dag=dag
    )

    crude_modifications = group_kvs_into_dict(
        chain.from_iterable(map(get_node_replacements, var_nodes))
    )

    for func_node in dag.func_nodes:
        if modifications := crude_modifications.get(func_node.name, None):
            grouped_modifications = group_kvs_into_dict(modifications)
            argument_names = grouped_modifications.get(VarNodeRole.argument, [])
            return_name = _get_first_if_any_and_asserting_unique(
                iterable=grouped_modifications.get(VarNodeRole.return_value, []),
                default=None,
                msg=f"You shouldn't have more than one return_value in {func_node}",
            )
            yield func_node, tuple(argument_names), return_name
        else:
            yield func_node, (), None


def _mk_param_to_mall_map_from_for_var_nodes(
    var_nodes, bind, var_node_name_to_store_name
):
    """Generate (param, store_name) pairs.

    >>> dict(
    ...     _mk_param_to_mall_map_from_for_var_nodes(
    ...         var_nodes=['a', 'c'],
    ...         bind={'w': 'a', 'x': 'c', 'y': 'c', 'z': 'b'},
    ...         var_node_name_to_store_name=lambda name: f"{name}_store"
    ...     )
    ... )
    {'w': 'a_store', 'x': 'c_store', 'y': 'c_store'}
    """
    for param, var_node in bind.items():
        if var_node in var_nodes:
            yield param, var_node_name_to_store_name(var_node)


def _return_save_name(*, save_name) -> str:
    return save_name


def _empty_name_callback():
    raise RuntimeError(f'No save name was given')


from i2.wrapper import rm_params


def _crudified_func_nodes(
    var_nodes: Union[str, Iterable[str]],
    dag: DAG,
    var_node_name_to_store_name=partial(simple_namer, suffix='_store'),
    *,
    mall: Union[Mapping[str, Mapping[str, Any]], None] = None,
    include_stores_attribute: bool = False,
    save_name_param: str = 'save_name',
):
    if isinstance(var_nodes, str):
        var_nodes = var_nodes.split()
    # make a mall for all the var_names, giving them all empty dicts as stores if they are not there already.
    mall = mall or dict()
    mall = dict(
        {var_node_name_to_store_name(var_name): dict() for var_name in var_nodes},
        **mall,
    )
    rm_save_name = partial(rm_params, params_to_remove=[save_name_param])

    for (
        func_node,
        argument_names,
        return_name,
    ) in _func_nodes_arg_and_return_names_to_crude(var_nodes, dag):
        mk_param_mall_map = partial(
            _mk_param_to_mall_map_from_for_var_nodes,
            var_node_name_to_store_name=var_node_name_to_store_name,
        )
        if (argument_names, return_name) == ((), None):
            yield func_node
        else:
            param_to_mall_map = (
                dict(mk_param_mall_map(argument_names, func_node.bind)) or None
            )
            output_store = (
                var_node_name_to_store_name(return_name)
                if return_name is not None
                else None
            )

            crudified_func = prepare_for_crude_dispatch(
                func_node.func,
                param_to_mall_map=param_to_mall_map,
                output_store=output_store,
                empty_name_callback=None,
                auto_namer=lambda: f'{func_node.out}_last_output',
                output_trans=_return_save_name,
                mall=mall,
                include_stores_attribute=include_stores_attribute,
                save_name_param=save_name_param,
            )

            yield ch_func_node_attrs(func_node, func=rm_save_name(crudified_func))


# empty_name_callback: Callable[[], Any] = None,
# auto_namer: Callable[..., str] = None,
# output_trans: Callable[..., Any] = None,
