"""Integration tests for the function → pydantic-model → wrapped-call pipeline.

The unit test in :mod:`test_py2pydantic` only checks the *structure* of the
generated input model. This file checks the **end-to-end dispatch path** that
front and streamlitfront depend on:

  - generate a pydantic input model from a Python function
  - instantiate it with values (this exercises pydantic's coercion/validation)
  - feed it into the wrapped function and confirm the original function is
    invoked correctly and returns the expected result
  - confirm validation errors surface as ``ValidationError`` instead of
    silently passing through

If this file goes red after a pydantic version bump or signature change,
something has broken the contract that downstream front-based dispatch
relies on.
"""

import pytest
from pydantic import ValidationError

from front.py2pydantic import (
    func_to_pyd_input_model_cls,
    func_to_pyd_func,
    pydantic_model_from_type,
)


# Three of the four parameter kinds — the fourth (unannotated, default=None)
# is intentionally avoided here because pydantic v2 infers NoneType from a
# None default, which is a surprising-by-design behavior unrelated to dispatch.
def example(a: int, b: float = 1.5, d=10):
    return {"a": a, "b": b, "d": d, "sum": a + b + d}


def test_input_model_roundtrip_dispatch():
    """Build the input model, instantiate it, dispatch through the wrapper."""
    InputModel = func_to_pyd_input_model_cls(example)
    pyd_example = func_to_pyd_func(example)

    instance = InputModel(a=3, b=2.5)
    result = pyd_example(instance)

    assert result == {"a": 3, "b": 2.5, "d": 10, "sum": 15.5}


def test_input_model_coerces_types():
    """Pydantic should coerce a stringified int into an int per the annotation."""
    InputModel = func_to_pyd_input_model_cls(example)
    # "5" is coerced to int 5 by pydantic (lax mode is the v2 default)
    instance = InputModel(a="5", b=0.0)
    assert instance.a == 5
    assert isinstance(instance.a, int)


def test_input_model_raises_on_invalid_type():
    """Pydantic should raise ValidationError when input can't be coerced."""
    InputModel = func_to_pyd_input_model_cls(example)
    with pytest.raises(ValidationError):
        InputModel(a="not-an-int", b=0.0)


def test_input_model_missing_required():
    """Missing a required field surfaces as ValidationError, not a silent pass."""
    InputModel = func_to_pyd_input_model_cls(example)
    with pytest.raises(ValidationError):
        InputModel(b=0.0)  # missing `a`


def test_input_model_json_schema_shape():
    """The schema reflects the function signature's contract."""
    InputModel = func_to_pyd_input_model_cls(example)
    schema = InputModel.model_json_schema()
    assert schema["type"] == "object"
    # `a` is required, `b`/`c`/`d` have defaults
    assert "a" in schema["required"]
    assert "b" not in schema.get("required", [])
    # Annotated params carry their declared type
    assert schema["properties"]["a"]["type"] == "integer"
    assert schema["properties"]["b"]["type"] == "number"


def test_output_model_round_trip():
    """`pydantic_model_from_type` produces a model that wraps the chosen type."""
    OutputModel = pydantic_model_from_type(int, name="MyOutput", field_name="value")
    inst = OutputModel(value=42)
    assert inst.value == 42
    with pytest.raises(ValidationError):
        OutputModel(value="not-an-int-or-coercible")


def test_basemodel_name_conflict_handled():
    """Param names that collide with BaseModel attrs get auto-uppercased.

    Without this, pydantic emits a UserWarning *and* shadows the BaseModel
    attribute. The renaming keeps the model class clean.
    """
    import warnings

    def f(x, copy, schema):
        return (x, copy, schema)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        InputModel = func_to_pyd_input_model_cls(f, warn_when_changing_names=False)

    fields = set(InputModel.model_fields)
    assert fields == {"x", "COPY", "SCHEMA"}
