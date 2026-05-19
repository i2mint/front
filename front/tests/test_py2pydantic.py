"""Unit tests for :mod:`front.py2pydantic`."""

from pydantic_core import PydanticUndefined

from front.py2pydantic import *


# This one has every of the 4 combinations of (default y/n, annotated y/n)
# def formula1(w, /, x: float, y=1, *, z: int = 1):
def formula1(w, x: float, y=1, z: int = 1):
    return ((w + x) * y) ** z


def test_func_to_pyd_model_of_inputs(func: Callable = formula1, dflt_type=Any):
    pyd_model = func_to_pyd_input_model_cls(func, dflt_type)
    sig = Sig(func)
    # The function arg names should match the model's field names.
    assert sorted(sig.names) == sorted(pyd_model.model_fields)
    # And for each field, default and annotation should match the signature.
    for name, model_field in pyd_model.model_fields.items():
        param = sig.parameters[name]
        if param.default is empty_param_attr:
            # No default → pydantic marks the field required (PydanticUndefined sentinel).
            assert model_field.default is PydanticUndefined
            assert model_field.is_required()
        else:
            assert model_field.default == param.default
            assert not model_field.is_required()
        if param.annotation is not empty_param_attr:
            # If arg is annotated, expect that as the field type.
            assert model_field.annotation == param.annotation
        elif param.default is empty_param_attr:
            # If arg is not annotated and has no default, expect dflt_type.
            assert model_field.annotation == dflt_type
        # else: pydantic infers the type from the default's type — we don't pin that here.
