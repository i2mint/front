from dataclasses import dataclass
from typing import Any, Callable, Mapping, Union

Map = Union[None, Mapping, Callable[[], Mapping]]
Configuration = Mapping
Convention = Mapping
FrontElementName = Union[None, str, Callable[[Any], str]]


@dataclass
class FrontSpec:
    app_spec: dict
    obj_spec: dict
    rendering_spec: dict


FrontApp = Callable
