"""Type aliases and lightweight dataclasses shared across front modules.

Centralizes the names used in spec compilation (``Configuration``,
``Convention``, ``Map``) and the structured :class:`FrontSpec` consumed by
:class:`~front.app_maker.AppMaker`.
"""

from dataclasses import dataclass
from typing import Any, Union
from collections.abc import Callable, Mapping

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
