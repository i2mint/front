"""Tools to dispatch dags

See below one of the dags that will often be used in this module's doctests:

>>> from meshed.makers import code_to_dag
>>> @code_to_dag
... def dag():
...     a = get_a()
...     x = foo(a, b, c)
...     y = bar(x, greeting)
...     z = confuser(a, w=x)  # note the w=x to test non-trivial binding
>>> print(dag.dot_digraph_ascii())  # doctest: +SKIP
..
                             b

                          │
                          │
                          ▼
                        ┌──────────┐
             c      ──▶ │   foo    │ ◀┐
                        └──────────┘  │
                          │           │
                          │           │
                          ▼           │
                                      │
      ┌────────────────      x        │
      │                               │
      │                   │           │
      │                   │           │
      │                   ▼           │
      │                 ┌──────────┐  │
      │   greeting  ──▶ │   bar    │  │
      │                 └──────────┘  │
      │                   │           │
      │                   │           │
      │                   ▼           │
      │                               │
      │                      y        │
      │                               │
      │                 ┌──────────┐  │
      │                 │  get_a   │  │
      │                 └──────────┘  │
      │                   │           │
      │                   │           │
      │                   ▼           │
      │                               │
      │                      a       ─┘
      │
      │                   │
      │                   │
      │                   ▼
      │                 ┌──────────┐
      └───────────────▶ │ confuser │
                        └──────────┘
                          │
                          │
                          ▼

                             z


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


class VarNodeRole(Enum):
    argument = 'argument'
    return_value = 'return_value'


def _get_returned_by_func_node(var_node: str, dag: DAG):
    returned_by_func_node = parents(dag.graph, var_node)
    if len(returned_by_func_node) > 1:
        raise ValueError(
            f"This var_node had more than one parent. That is shouldn't be possible: "
            f'{var_node}'
        )
    elif len(returned_by_func_node) == 0:
        raise NotImplementedError(
            f'For time being, you can only crudify intermediate var nodes, not root '
            f'ones like: {var_node}'
        )
    return next(iter(returned_by_func_node))


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
    ...     a = get_a()
    ...     x = foo(a, b, c)
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
    _validate_is_func_node(returned_by_func_node, var_node, 'Parent')
    yield returned_by_func_node.name, (VarNodeRole.return_value, var_node)

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

    >>> from meshed.makers import code_to_dag
    >>> @code_to_dag
    ... def dag():
    ...     a = get_a()
    ...     x = foo(a, b, c)
    ...     y = bar(x, greeting)
    ...     z = confuser(a, w=x)  # note the w=x to test non-trivial binding
    >>>
    >>> # Showing but skipping (because I can't get order to be stable (TODO: Make it so)
    >>> sorted(
    ... _func_nodes_arg_and_return_names_to_crude(['x', 'a'], dag)
    ... )  # doctest: +SKIP
    [
        (FuncNode(a,x -> confuser -> z), ('x', 'a'), None),
        (FuncNode( -> get_a -> a), (), 'a'),
        (FuncNode(x,greeting -> bar -> y), ('x',), None),
        (FuncNode(a,b,c -> foo -> x), ('a',), 'x')
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


def _return_save_name(*, save_name):
    return save_name


def _empty_name_callback():
    raise RuntimeError(f'No save name was given')


def simple_namer(name, *, prefix='', suffix=''):
    return f'{prefix}{name}{suffix}'


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
    mall = mall or defaultdict(dict)
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
        if (argument_names, return_name) == ((), ()):
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


def crudify_func_nodes(
    var_nodes: Union[str, Iterable[str]],
    dag: DAG,
    var_node_name_to_store_name=partial(simple_namer, suffix='_store'),
    *,
    mall: Union[Mapping[str, Mapping[str, Any]], None] = None,
    include_stores_attribute: bool = False,
    save_name_param: str = 'save_name',
):
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


# empty_name_callback: Callable[[], Any] = None,
# auto_namer: Callable[..., str] = None,
# output_trans: Callable[..., Any] = None,
