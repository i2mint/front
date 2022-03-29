from itertools import chain
from typing import Any, Callable, ContextManager, Iterable, Mapping
from meshed.makers import code_to_dag
from front.dag import crudify_func_nodes

from front.tests.util import get_var_nodes_to_crudify, rdm_int, rdm_str

#####################
## SIMPLE USE CASE ##
#####################


def simple_use_case():
    x = foo(a, b, c)
    y = bar(x, greeting)
    z = confuser(a, x)


def foo_func(a: int = 0, b: int = 0, c=0) -> int:
    """This is foo. It computes something"""
    return (a * b) + c


def bar_func(x: str, greeting='hello') -> str:
    """bar greets its input"""
    return f'{greeting} {x}'


def confuser_func(a: int = 0, x: float = 3.14) -> float:
    return (a ** 2) * x


########################
## RUN MODEL USE CASE ##
########################


def run_model_use_case():
    wfs = get_wfs(src_to_wf, data_src)
    chks = get_chunks(chunker, wfs)
    fvs = get_fvs(featurizer, chks)
    model_outputs = run_model(model, fvs)


def get_wfs_func(src_to_wf: Callable, data_src: int) -> Iterable[Iterable[int]]:
    return src_to_wf(data_src)


def get_chunks_func(
    chunker: Callable, wfs: Iterable[Iterable[int]]
) -> Iterable[Iterable[int]]:
    return chain.from_iterable(map(chunker, wfs))


def get_fvs_func(featurizer: Callable, chks: Iterable[Iterable[int]]):
    return map(featurizer, chks)


def run_model_func(model: Callable, fvs: Iterable[int]) -> Iterable[str]:
    return list(map(model, fvs))


def src_to_wf_func(src):
    for i in range(src):
        yield [i, i + 2, i * 3, i + 5]


def chunker_func(wf):
    yield wf[0:2]
    yield wf[2:4]


featurizer_func = sum


def model_func(x):
    return f'hi {x}'


###########
## TESTS ##
###########

TEST_USE_CASE_PARAMETER_NAMES = 'use_case, func_src, kwargs'
TEST_USE_CASE_PARAMETERS = [
    (
        simple_use_case,
        {'foo': foo_func, 'bar': bar_func, 'confuser': confuser_func,},
        {'a': rdm_int(), 'b': rdm_int(), 'c': rdm_int(), 'greeting': rdm_str(),},
    ),
    # BUG: The execution of a crudified func node through front returns the result
    # of the initial function instead of the key used to store the result.
    # (
    #     run_model_use_case,
    #     {
    #         'get_wfs': get_wfs_func,
    #         'get_chunks': get_chunks_func,
    #         'get_fvs': get_fvs_func,
    #         'run_model': run_model_func,
    #     },
    #     {
    #         'data_src': 5,
    #         'src_to_wf': src_to_wf_func,
    #         'chunker': chunker_func,
    #         'featurizer': featurizer_func,
    #         'model': model_func,
    #     },
    # ),
]


def base_test_use_case(
    use_case: Callable,
    func_src: Mapping[str, Callable],
    inputs: Mapping[str, Any],
    mk_front_func: Callable,
    run_front_app: ContextManager,
):
    def mk_crudified_dag():
        mall = dict()
        for k, v in inputs.items():
            if k in var_nodes_to_crudify:
                store_key = str(v)
                mall[f'{k}_store'] = {store_key: v}
                front_dag_inputs[k] = store_key
        return crudify_func_nodes(var_nodes_to_crudify, dag, mall=mall)

    dispatch_func_src = dict(func_src)
    var_nodes_to_crudify = get_var_nodes_to_crudify(dispatch_func_src.values())
    front_dag_inputs = dict(inputs)
    if var_nodes_to_crudify:
        crudified_dag = mk_crudified_dag()
        dispatch_func_src = {
            func_node.name: func_node.func for func_node in crudified_dag.func_nodes
        }
    dispatch_funcs = list(dispatch_func_src.values())
    with run_front_app(dispatch_funcs) as front_app:
        front_func_src = {
            node_name: mk_front_func(func, dispatch_funcs, front_app)
            for node_name, func in dispatch_func_src.items()
        }
        dag = code_to_dag(use_case, func_src=func_src)
        front_dag = code_to_dag(use_case, func_src=front_func_src)
        assert front_dag(**front_dag_inputs) == dag(**inputs)
