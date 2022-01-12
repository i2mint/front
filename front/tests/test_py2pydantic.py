from pydantic.main import create_model
import pytest
from i2 import Sig
from pydantic import create_model
from i2.tests.objects_for_testing import formula1
from front.scrap.py2pydantic import func_to_pyd_model_specs, func_to_pyd_input_model_cls
import typing


def test_func_to_pyd_model_specs():
    result = list(func_to_pyd_model_specs(func=formula1, dflt_type=typing.Any))
    expected = [
        ("w", (typing.Any, Ellipsis)),
        ("x", (float, Ellipsis)),
        ("y", 1),
        ("z", (int, 1)),
    ]
    assert result == expected


def test_func_to_pyd_input_model_cls():
    pyd_model = func_to_pyd_input_model_cls(formula1)
    result_schema = pyd_model.schema()
    expected_schema = {
        "title": "formula1",
        "type": "object",
        "properties": {
            "w": {"title": "W"},
            "x": {"title": "X", "type": "number"},
            "z": {"title": "Z", "default": 1, "type": "integer"},
            "y": {"title": "Y", "default": 1, "type": "integer"},
        },
        "required": ["w", "x"],
    }
    assert result_schema == expected_schema
