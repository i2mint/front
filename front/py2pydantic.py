"""How do we eliminate some of the boilerplate between having python functions
and making them pydantic?

>>> from i2.tests.objects_for_testing import formula1
>>> pyd_input_model = func_to_pyd_input_model_cls(formula1)
>>> pyd_input_model
<class 'pydantic.main.formula1'>
>>> from i2 import Sig
>>> Sig(formula1)
<Sig (w, /, x: float, y=1, *, z: int = 1)>
>>> Sig(pyd_input_model)
<Sig (*, w: Any, x: float, z: int = 1, y: int = 1) -> None>

>>> pyd_func = func_to_pyd_func(formula1)
>>> input_model_instance = pyd_input_model(w=1, x=2)
>>> input_model_instance
formula1(w=1, x=2.0, z=1, y=1)
>>> pyd_func(input_model_instance)
3.0
>>> formula1(1, x=2)  # can't say w=1 because w is position only
3

"""

from typing import Callable, Any
from functools import partial

from pydantic import create_model
from i2 import Sig, name_of_obj, empty_param_attr
from i2.wrapper import wrap


def pyd_func_ingress_template(input_model_instance, wrapped_func_sig: Sig):
    kwargs = dict(input_model_instance)
    args, kwargs = wrapped_func_sig.args_and_kwargs_from_kwargs(kwargs)
    return args, kwargs


# TODO: Add the output model annotation
def func_to_pyd_func(func: Callable, dflt_type=Any):
    """Get a 'opyrator' function from a python function.
    That is, a function that has a single pydantic model input and output.
    """
    pyd_func_ingress = partial(pyd_func_ingress_template, wrapped_func_sig=Sig(func))

    input_model = func_to_pyd_input_model_cls(func, dflt_type)
    output_model = create_model(
        'output_model', output_val=(Any, ...)
    )  # TODO: Work on this
    # TODO: Inject annotations in pyd_func_ingress

    return wrap(func, ingress=pyd_func_ingress)


def func_to_pyd_input_model_cls(func: Callable, dflt_type=Any, name=None):
    """Get a pydantic model of the arguments of a python function"""
    name = name or name_of_obj(func)
    return create_model(name, **dict(func_to_pyd_model_specs(func, dflt_type)))


def func_to_pyd_model_specs(func: Callable, dflt_type=Any):
    """Helper function to get field info from python signature parameters"""
    for p in Sig(func).params:
        if p.annotation is not empty_param_attr:
            if p.default is not empty_param_attr:
                yield p.name, (p.annotation, p.default)
            else:
                yield p.name, (p.annotation, ...)
        else:  # no annotations
            if p.default is not empty_param_attr:
                yield p.name, p.default
            else:
                yield p.name, (dflt_type, ...)


def pydantic_egress(output):
    return_type = type(output)
    mod = create_model('Output', output_val=return_type)

    return mod(output_val=output)
