from abc import ABC, abstractclassmethod
from typing import Any, Iterable
from front.elements.elements import (
    ELEMENT_KEY,
    FrontContainerBase,
)
from front.util import deep_merge


class ElementTreeMaker:
    """Takes care of generating the composite tree of elements based on the "rendering"
    specification previously compiled from the configuration. This composite tree will
    then be used to build the application by rendering each element recursively from
    the root of the tree (the App container).
    """

    def mk_tree(
        self, front_objs: Iterable[Any], rendering_spec: dict
    ) -> FrontContainerBase:
        """Entrypoint of the ElementTreeMaker class. Builds the composite tree
        
        :param front_objs: The objects to render after transformation (see AppMaker).
        :param rendering_spec: The rendering spec of the application, compiled from
            the given configuration.
            This nested object contains information on how an object should be rendered
            based on its type (general spec that can be reused for several objects) or
            its name (specific spec for a single object). Both specs can be used for a
            single objects. In that case, the spec that will be used for this object
            will be a combination between those two specs (any value in the specific
            spec overwrites the value in the general spec for any key that they could
            have in common).
        """
        self.front_objs = front_objs
        self.rendering_spec = dict(rendering_spec)
        root_factory = self._get_root_factory()
        obj_rendering_specs = {k: v for k, v in self._gen_obj_rendering_specs()}
        root: FrontContainerBase = root_factory(**obj_rendering_specs)
        return root

    def _get_root_factory(self):
        root_factory = self.rendering_spec.pop(ELEMENT_KEY)
        if not root_factory:
            raise RuntimeError(
                'No app element has been defined for this front application.'
            )
        return root_factory

    def _gen_obj_rendering_specs(self):
        for obj in self.front_objs:
            obj_name = obj.__name__
            type_rendering_spec = self._get_type_rendering_spec(
                self.rendering_spec, obj
            )
            obj_rendering_spec = self.rendering_spec.get(obj.__name__, {})
            obj_rendering_spec = deep_merge(type_rendering_spec, obj_rendering_spec)
            obj_rendering_spec['obj'] = obj
            yield (obj_name, obj_rendering_spec)

    def _get_type_rendering_spec(self, spec: dict, obj):
        obj_type = type(obj)
        obj_type_spec = spec.get(obj_type)
        if obj_type_spec:
            return obj_type_spec
        if getattr(obj_type, 'mro'):
            for t in obj_type.mro():
                type_spec = spec.get(t)
                if type_spec:
                    return type_spec
        for k, v in spec.items():
            if isinstance(obj, k):
                return v
        return {}
