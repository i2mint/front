from dataclasses import dataclass
from typing import Any, Callable, Mapping, Union

Map = Union[None, Mapping, Callable[[], Mapping]]
Configuration = Mapping
Convention = Mapping
FrontElementName = Union[None, str, Callable[..., str]]
FrontElementDisplay = Union[bool, Callable[..., bool]]


@dataclass
class FrontSpec:
    app_spec: dict
    obj_spec: dict
    rendering_spec: dict


FrontApp = Callable
