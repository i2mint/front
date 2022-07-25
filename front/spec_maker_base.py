from abc import abstractclassmethod
import collections.abc
from inspect import isclass
from typing import Any, Mapping
from front.types import FrontSpec, Map
from front.util import deep_merge, dflt_name_trans, dflt_trans, normalize_map
from front.elements import *


APP_KEY = 'app'
OBJ_KEY = 'obj'
RENDERING_KEY = 'rendering'
NAME_KEY = 'name'

BASE_DFLT_CONVENTION = {
    APP_KEY: {'title': 'My Front Application'},
    OBJ_KEY: {'trans': dflt_trans},
    RENDERING_KEY: {
        collections.abc.Callable: {
            NAME_KEY: dflt_name_trans,
            'description': {NAME_KEY: 'Description', 'content': lambda o: o.__doc__,},
            'execution': {
                NAME_KEY: 'Execution',
                'inputs': {
                    float: {'format': '%.2f', 'step': 0.01,},
                    DEFAULT_INPUT_KEY: {NAME_KEY: lambda p: p.name},
                },
                'output': {NAME_KEY: 'Output',},
            },
        }
    },
}


class SpecMakerBase(ABC):
    def mk_spec(self, config: Map, convention: Map = None) -> FrontSpec:
        def get_inheritance_path(cls):
            path = []
            for cls_key in cls_keys:
                if cls != cls_key and issubclass(cls, cls_key):
                    i = 0
                    while i < len(path) and issubclass(path[i], cls_key):
                        i += 1
                    path.insert(i, cls_key)
            return path

        config = normalize_map(config)
        if convention is None:
            convention = deep_merge(BASE_DFLT_CONVENTION, self._dflt_convention)
        convention = normalize_map(convention)
        spec = deep_merge(convention, config)

        rendering_spec = spec.get('rendering', {})
        cls_keys = [k for k in rendering_spec if isclass(k)]
        inheritance_paths = {cls: get_inheritance_path(cls) for cls in cls_keys}
        for cls, path in inheritance_paths.items():
            cls_spec = rendering_spec[cls]
            for subcls in path:
                subcls_spec = rendering_spec[subcls]
                cls_spec = deep_merge(subcls_spec, cls_spec)
            rendering_spec[cls] = cls_spec

        return FrontSpec(
            obj_spec=spec.get(OBJ_KEY, {}),
            rendering_spec=rendering_spec,
            app_spec=spec.get(APP_KEY, {}),
        )

    @property
    @abstractclassmethod
    def _dflt_convention(cls) -> Mapping:
        pass
