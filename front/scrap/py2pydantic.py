"""How do we eliminate some of the boiler plate between having python functions
and making them pydantic?

>>> from i2.tests.objects_for_testing import formula1
>>> test_func_to_pyd_model_of_inputs(formula1)
>>> pyd_model = func_to_pyd_model_of_inputs(formula1)
>>> pyd_model
<class 'pydantic.main.formula1'>
>>> from i2 import Sig
>>> Sig(formula1)
<Sig (w, /, x: float, y=1, *, z: int = 1)>
>>> Sig(pyd_model)
<Sig (*, w: Any, x: float, z: int = 1, y: int = 1) -> None>

"""

from typing import Callable, Any

from pydantic import BaseModel, create_model
from i2 import Sig, name_of_obj, empty_param_attr


def func_to_pyd_model_of_inputs(func: Callable, dflt_type=Any, name=None):
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


# ---------------------------------------------------------------------------------------
# Tests


def test_func_to_pyd_model_of_inputs(func: Callable, dflt_type=Any):
    pyd_model = func_to_pyd_model_of_inputs(func, dflt_type)
    sig = Sig(func)
    # # TODO: Don't want to use hidden __fields__. Other "official" access to this info?
    # the names of the arguments should correspond to names of the model's fields:
    assert sorted(sig.names) == sorted(pyd_model.__fields__)
    # and for each field, name, default, and sometimes annotations/types should match...
    for name, model_field in pyd_model.__fields__.items():
        param = sig.parameters[name]
        expected_default = (
            param.default if param.default is not empty_param_attr else None
        )
        if param.annotation is not empty_param_attr:
            # if arg is annotated, expect that as the field type
            assert model_field.type_ == param.annotation
        elif param.default is empty_param_attr:
            # if arg is not annotated and doesn't have a default, expect dflt_type
            assert model_field.type_ == dflt_type
        # but don't test pydantic's resolution of types from default values


