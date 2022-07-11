import collections.abc
from inspect import isclass
from typing import Any
from front.types import FrontSpec, Map
from front.util import deep_merge, dflt_name_trans, dflt_trans, normalize_map
from front.elements import *

# def dflt_convention():
#     return {
#         'app': {'title': 'My Front Application'},
#         'obj': {'trans': dflt_trans},
#         'rendering': {
#             Callable: {
#                 'container': VIEW_CONTAINER,
#                 'execution': {
#                     'container': EXEC_SECTION_CONTAINER,
#                     'name': 'Execution',
#                     'inputs': {
#                         int: {'component': INT_INPUT_COMPONENT,},
#                         float: {
#                             'component': FLOAT_INPUT_COMPONENT,
#                             'format': '%.2f',
#                             'step': 0.01,
#                         },
#                         Any: {'component': TEXT_INPUT_COMPONENT,},
#                     },
#                 },
#                 'image': {
#                     'container': SECTION_CONTAINER,
#                     'name': 'Image',
#                 },
#             },
#         },
#     }

APP_KEY = 'app'
OBJ_KEY = 'obj'
RENDERING_KEY = 'rendering'
NAME_KEY = 'name'
DEFAULT_INPUT_KEY = '_default'

DFLT_CONVENTION = {
    APP_KEY: {'title': 'My Front Application'},
    OBJ_KEY: {'trans': dflt_trans},
    RENDERING_KEY: {
        collections.abc.Callable: {
            ELEMENT_KEY: VIEW_CONTAINER,
            NAME_KEY: dflt_name_trans,
            'execution': {
                ELEMENT_KEY: EXEC_SECTION_CONTAINER,
                NAME_KEY: 'Execution',
                'inputs': {
                    int: {ELEMENT_KEY: INT_INPUT_COMPONENT,},
                    float: {
                        ELEMENT_KEY: FLOAT_INPUT_COMPONENT,
                        'format': '%.2f',
                        'step': 0.01,
                    },
                    Any: {ELEMENT_KEY: TEXT_INPUT_COMPONENT,},
                    DEFAULT_INPUT_KEY: {NAME_KEY: lambda p: p.name},
                },
            },
        }
    },
}


class SpecMaker:
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
        convention = convention or DFLT_CONVENTION
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
