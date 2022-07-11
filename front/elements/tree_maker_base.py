from abc import ABC, abstractclassmethod
from typing import Any, Iterable, Mapping
from front.elements.elements import (
    APP_CONTAINER,
    ELEMENT_KEY,
    STORED_VALUE_GETTER,
    FrontElementBase,
    FrontContainerBase,
)
from front.util import deep_merge


class ElementTreeMakerBase(ABC):
    def mk_tree(
        self, front_objs: Iterable[Any], rendering_spec: dict
    ) -> FrontContainerBase:
        self.front_objs = front_objs
        self.rendering_spec = self._inject_components(rendering_spec)
        root_factory = self._get_root_factory()
        obj_rendering_specs = {k: v for k, v in self._gen_obj_rendering_specs()}
        root: FrontContainerBase = root_factory(**obj_rendering_specs)
        return root

    def _inject_components(self, spec_node: dict):
        _spec_node = dict(spec_node)
        for key, value in spec_node.items():
            if isinstance(value, Mapping):
                new_value = self._inject_components(value)
            elif key == ELEMENT_KEY and isinstance(value, str):
                new_value = self._element_mapping[value]
            else:
                new_value = value
            _spec_node[key] = new_value
        return _spec_node

    def _get_root_factory(self):
        root_factory = self._element_mapping.get(APP_CONTAINER)
        if not root_factory:
            raise RuntimeError(
                'No app element as been defined for this front application.'
            )
        return root_factory

    def _gen_obj_rendering_specs(self):
        for obj in self.front_objs:
            setattr(obj, STORED_VALUE_GETTER, self._get_stored_value)
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

    @property
    @abstractclassmethod
    def _element_mapping(cls) -> Mapping[int, FrontElementBase]:
        pass

    @abstractclassmethod
    def _get_stored_value(cls, key: str) -> Any:
        pass
