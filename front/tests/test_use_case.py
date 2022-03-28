from itertools import chain
from typing import Callable, Iterable
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
    # (
    #     simple_use_case,
    #     {
    #         'foo': foo_func,
    #         'bar': bar_func,
    #         'confuser': confuser_func,
    #     },
    #     {
    #         'a': rdm_int(),
    #         'b': rdm_int(),
    #         'c': rdm_int(),
    #         'greeting': rdm_str(),
    #     },
    # ),
    (
        run_model_use_case,
        {
            'get_wfs': get_wfs_func,
            'get_chunks': get_chunks_func,
            'get_fvs': get_fvs_func,
            'run_model': run_model_func,
        },
        {
            'data_src': 5,
            'src_to_wf': src_to_wf_func,
            'chunker': chunker_func,
            'featurizer': featurizer_func,
            'model': model_func,
        },
    ),
]


def base_test_use_case(
    use_case, func_src, inputs, mk_front_func, **mk_front_func_kwargs
):
    front_func_src = {
        node_name: mk_front_func(func, **mk_front_func_kwargs)
        for node_name, func in func_src.items()
    }
    front_dag = code_to_dag(use_case, func_src=front_func_src)
    var_nodes_to_crudify = get_var_nodes_to_crudify(front_func_src.values())
    if var_nodes_to_crudify:
        front_dag = crudify_func_nodes(var_nodes_to_crudify, front_dag)
    dag = code_to_dag(use_case, func_src=func_src)
    for kwargs in inputs:
        assert front_dag(**kwargs) == dag(**kwargs)
