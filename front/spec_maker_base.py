"""Base classes and conventions for building a :class:`~front.types.FrontSpec` from a configuration.

A spec maker is the "short language → long language" compiler of front: it
consumes a user configuration plus a convention (defaults) and emits the
nested ``app`` / ``obj`` / ``rendering`` specification consumed by
:class:`~front.app_maker.AppMaker`.
"""

from abc import abstractclassmethod
import collections.abc
from inspect import isclass
from typing import Any
from collections.abc import Mapping
from front.types import FrontSpec, Map
from front.util import deep_merge, dflt_name_trans, dflt_trans, normalize_map
from front.elements import *


APP_KEY = "app"
OBJ_KEY = "obj"
RENDERING_KEY = "rendering"
NAME_KEY = "name"

BASE_DFLT_CONVENTION = {
    APP_KEY: {"title": "My Front Application"},
    OBJ_KEY: {"trans": dflt_trans},
    RENDERING_KEY: {
        collections.abc.Callable: {
            NAME_KEY: dflt_name_trans,
            "description": {
                NAME_KEY: "Description",
                "content": lambda o: o.__doc__,
            },
            "execution": {
                NAME_KEY: "Execution",
                "inputs": {
                    float: {
                        "format": "%.2f",
                        "step": 0.01,
                    },
                    DEFAULT_INPUT_KEY: {
                        NAME_KEY: lambda p: p.name.replace("_", " ").title()
                    },
                },
                "output": {
                    NAME_KEY: "Output",
                },
            },
        }
    },
}


class SpecMakerBase(ABC):
    """Compile a user configuration (short language) into a ``FrontSpec`` (long language).

    The configuration is merged over a convention (the defaults), then the
    class-keyed entries of the rendering specification are completed along the
    class hierarchy, so that a spec for a subclass inherits the spec of its bases.

    To do so, the "mk_spec" method first merges the configuration with the convention,
    then does the following for the rendering specification:
    Let's consider we have three classes A, B and C with C extends B and B extends A
    (A <- B <- C). If the rendering configuration contains the following::

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

    The resulting rendering specification will be::

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

    >>> from front import APP_KEY, OBJ_KEY, RENDERING_KEY
    >>> from front.util import dflt_trans
    >>> class A: pass
    >>> class B(A): pass
    >>> class C(B): pass
    >>> class SpecMaker(SpecMakerBase):
    ...     @property
    ...     def _dflt_convention(self):
    ...         return {
    ...             APP_KEY: {'title': 'Untitled'},
    ...             OBJ_KEY: {'trans': dflt_trans},
    ...             RENDERING_KEY: {A: {'a': 1}, B: {'b': 2}, C: {'c': 3}},
    ...         }
    >>> spec = SpecMaker().mk_spec({APP_KEY: {'title': 'Demo'}})
    >>> spec.app_spec
    {'title': 'Demo'}
    >>> spec.rendering_spec[C]
    {'a': 1, 'b': 2, 'c': 3}
    >>> spec.rendering_spec[B]
    {'a': 1, 'b': 2}

    See Also:
        ``front.app_maker.AppMaker``: consumes the spec this class produces.
        ``front.util.deep_merge``: the merge used for config over convention.
    """

    def mk_spec(self, config: Map, convention: Map = None) -> FrontSpec:
        """Merge ``config`` over ``convention`` and complete class-keyed rendering specs.

        :param config: The user configuration: a mapping, a callable returning one,
            or None (empty).
        :param convention: The defaults. If None, ``self._dflt_convention`` is used.
        :return: A ``FrontSpec`` with ``app_spec``, ``obj_spec`` and ``rendering_spec``.
        """

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

        rendering_spec = spec.get("rendering", {})
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
        """IMPORTANT! This property needs to be overloaded in concrete subclasses."""
        pass
