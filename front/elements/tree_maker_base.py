from abc import ABC, abstractclassmethod
from typing import Any, Iterable
from front.elements.elements import (
    ELEMENT_KEY,
    FrontContainerBase,
)
from front.util import deep_merge


class ElementTreeMaker:
    def mk_tree(
        self, front_objs: Iterable[Any], rendering_spec: dict
    ) -> FrontContainerBase:
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
