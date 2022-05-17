from typing import Any, Callable, Mapping, Union

Map = Union[None, Mapping, Callable[[], Mapping]]
Configuration = Mapping
Convention = Mapping


class FrontSpec:
    def __init__(self, obj_spec: dict, rendering_spec: dict, app_spec: dict):
        self.obj_spec = obj_spec
        self.rendering_spec = rendering_spec
        self.app_spec = app_spec


FrontApp = Callable
