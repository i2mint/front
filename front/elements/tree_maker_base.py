from abc import ABC, abstractclassmethod
from inspect import _empty
from typing import Any, Callable, Iterable, Mapping
from i2 import Sig
from meshed import DAG
from front.elements.element_flags import APP_CONTAINER
from front.elements.elements import (
    NamedContainerBase,
    FrontElementBase,
    FrontContainerBase,
)
from front.util import deep_merge, dflt_name_trans


class ElementTreeMakerBase(ABC):
    def mk_tree(
        self, front_objs: Iterable[Any], rendering_spec: dict
    ) -> NamedContainerBase:
        _rendering_spec = self._inject_components(rendering_spec)
        root_factory = self._element_mapping.get(APP_CONTAINER)
        if not root_factory:
            raise RuntimeError(
                'No app element as been defined for this front application.'
            )
        views = list(self._gen_views(front_objs, _rendering_spec))
        root: FrontContainerBase = root_factory(views)
        return root

    def _inject_components(self, spec_node):
        _spec_node = dict(spec_node)
        for key, value in spec_node.items():
            if isinstance(value, Mapping):
                new_value = self._inject_components(value)
            elif key in ('container', 'component'):
                new_value = self._element_mapping[value]
            else:
                new_value = value
            _spec_node[key] = new_value
        return _spec_node

    def _gen_views(self, front_objs, spec):
        for obj in front_objs:
            type_rendering_spec = self._get_type_rendering_spec(spec, obj)
            obj_rendering_spec = spec.get(obj.__name__, {})
            obj_rendering_spec = deep_merge(type_rendering_spec, obj_rendering_spec)
            view_factory = obj_rendering_spec['container']
            view_name = obj_rendering_spec.get('name', dflt_name_trans(obj))
            elements = list(self._gen_view_elements(obj, obj_rendering_spec))
            yield view_factory(elements, view_name)

    def _get_type_rendering_spec(self, spec, obj):
        for k, v in spec.items():
            if isinstance(obj, k):
                return v
        return {}

    def _gen_view_elements(self, obj, obj_rendering_spec):
        if isinstance(obj, DAG):
            exec_spec = obj_rendering_spec['execution']
            exec_container_factory = exec_spec['container']
            exec_container_name = exec_spec['name']
            inputs_spec = exec_spec['inputs']
            input_components = list(self._gen_input_components(obj, inputs_spec))
            yield exec_container_factory(obj, input_components, exec_container_name)

            graph_spec = dict(obj_rendering_spec['graph'])
            display_for_single_node = graph_spec.pop('display_for_single_node')
            display_graph = graph_spec.pop('display') and (
                len(obj.func_nodes) > 1 or display_for_single_node
            )
            if display_graph:
                container_factory = graph_spec.pop('container')
                container_name = graph_spec.pop('name')
                graph_factory = graph_spec.pop('component')
                graph_kwargs = dict(figure_or_dot=obj.dot_digraph(), **graph_spec)
                graph = graph_factory(**graph_kwargs)
                yield container_factory([graph], container_name)
        else:
            raise NotImplementedError('Only DAG front objects are supported for now')

    def _gen_input_components(self, obj, inputs_spec):
        sig = Sig(obj)
        for p in sig.params:
            label = p.name
            input_key = f'{obj.__name__}_{label}'
            stored_value = self._get_stored_value(input_key)
            init_value = (
                stored_value
                if stored_value is not None
                else (p.default if p.default != _empty else None)
            )
            input_kwargs = dict(
                label=p.name, input_key=input_key, init_value=init_value
            )
            annot = p.annotation if p.annotation != _empty else None
            param_type = annot or (type(p.default) if p.default != _empty else Any)
            input_spec = inputs_spec.get(p.name)
            if not input_spec:
                input_spec = inputs_spec.get(param_type)
            if not input_spec:
                input_spec = inputs_spec[Any]
            if isinstance(input_spec, Mapping):
                input_spec = dict(input_spec)  # Make a copy before popping
                input_factory = input_spec.pop('component')
                input_kwargs = dict(input_kwargs, **input_spec)
            else:
                input_factory = input_spec
            yield input_factory(**input_kwargs)

    @property
    @abstractclassmethod
    def _element_mapping(cls) -> Mapping[int, FrontElementBase]:
        pass

    @abstractclassmethod
    def _get_stored_value(cls, key: str) -> Any:
        pass
