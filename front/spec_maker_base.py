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
                    DEFAULT_INPUT_KEY: {
                        NAME_KEY: lambda p: p.name.replace('_', ' ').title()
                    },
                },
                'output': {NAME_KEY: 'Output',},
            },
        }
    },
}


class SpecMakerBase(ABC):
    """This abstract class takes care of transforming the configuration given by the
    user (short language) to a detailed specification to build the application (long
    language).
    
    To do so, the "mk_spec" method first merges the configuration with the convention,
    then does the following for the rendering specification:
    Let's consider we have three classes A, B and C with C extends B and B extends A
    A <- B <- C.
    If the rendering configuration contains the following:
    {
        A: {
            'a': {...}
        },
        B: {
            'b': {...}
        },
        C: {
            'c': {...}
        },
    }
    The resulting rendering specification will be:
    {
        A: {
            'a': {...}
        },
        B: {
            'a': {...},
            'b': {...}
        },
        C: {
            'a': {...},
            'b': {...},
            'c': {...}
        },
    }

    This abstract class needs to be overloaded in every concrete front framework with
    a concrete implementation for the "_dflt_convention" property, which will return
    the convention after injecting the concrete element factories in it.
    """

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
            convention = self._dflt_convention
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
        """IMPORTANT! This property needs to be overloaded in concrete subclasses.
        """
        pass
