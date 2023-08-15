from front.py2pydantic import *

# ---------------------------------------------------------------------------------------
# Tests

# This one has every of the 4 combinations of (default y/n, annotated y/n)
# def formula1(w, /, x: float, y=1, *, z: int = 1):
def formula1(w, x: float, y=1, z: int = 1):
    return ((w + x) * y) ** z


def test_func_to_pyd_model_of_inputs(func: Callable = formula1, dflt_type=Any):
    pyd_model = func_to_pyd_input_model_cls(func, dflt_type)
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
        assert model_field.default == expected_default
        if param.annotation is not empty_param_attr:
            # if arg is annotated, expect that as the field type
            assert model_field.type_ == param.annotation
        elif param.default is empty_param_attr:
            # if arg is not annotated and doesn't have a default, expect dflt_type
            assert model_field.type_ == dflt_type
        # but don't test pydantic's resolution of types from default values
