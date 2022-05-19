from abc import ABC, abstractclassmethod
from inspect import _empty
from typing import Any, Callable, Iterable, Mapping
from front.elements.elements import (
    AppBase,
    ContainerFlag,
    InputComponentFlag,
    FrontElementBase,
    FrontContainerBase,
)
from i2 import Sig

from front.util import deep_merge


class ElementTreeMakerBase(ABC):
    def mk_tree(self, front_objs: Iterable[Any], rendering_spec: dict) -> AppBase:
        def inject_components(spec_node):
            _spec_node = dict(spec_node)
            for key, value in spec_node.items():
                if isinstance(value, Mapping):
                    new_value = inject_components(value)
                elif isinstance(value, InputComponentFlag):
                    new_value = self._component_mapping[value]
                elif isinstance(value, ContainerFlag):
                    new_value = self._container_mapping[value]
                else:
                    new_value = value
                _spec_node[key] = new_value
            return _spec_node

        def get_type_rendering_spec(obj):
            for k, v in _rendering_spec.items():
                if isinstance(obj, k):
                    return v
            return {}

        _rendering_spec = inject_components(rendering_spec)
        root_factory = self._container_mapping.get(ContainerFlag.APP)
        if not root_factory:
            raise RuntimeError(
                'No app element as been defined for this front application.'
            )
        obj_containers = []
        for obj in front_objs:
            type_rendering_spec = get_type_rendering_spec(obj)
            obj_rendering_spec = _rendering_spec.get(obj.__name__, {})
            obj_rendering_spec = deep_merge(type_rendering_spec, obj_rendering_spec)
            container_factory = type_rendering_spec['container']
            components = []
            if isinstance(obj, Callable):
                inputs_rendering_spec = obj_rendering_spec['inputs']
                sig = Sig(obj)
                for p in sig.params:
                    component_kwargs = dict(param=p)
                    annot = p.annotation if p.annotation != _empty else None
                    param_type = annot or (
                        type(p.default) if p.default != _empty else Any
                    )
                    component_spec = inputs_rendering_spec.get(p.name)
                    if not component_spec:
                        component_spec = inputs_rendering_spec.get(param_type)
                    if not component_spec:
                        component_spec = inputs_rendering_spec[Any]
                    if isinstance(component_spec, Mapping):
                        component_spec = dict(
                            component_spec
                        )  # Make a copy before popping
                        component_factory = component_spec.pop('component')
                        component_kwargs = dict(component_kwargs, **component_spec)
                    else:
                        component_factory = component_spec
                    component = component_factory(**component_kwargs)
                    components.append(component)
            else:
                raise NotImplementedError(
                    'Only callables front objects are supported for now'
                )
            container = container_factory(obj, components)
            obj_containers.append(container)
        root: FrontContainerBase = root_factory(obj_containers)
        return root

    @property
    @abstractclassmethod
    def _component_mapping(cls) -> Mapping[InputComponentFlag, FrontElementBase]:
        pass

    @property
    @abstractclassmethod
    def _container_mapping(cls) -> Mapping[ContainerFlag, FrontElementBase]:
        pass
