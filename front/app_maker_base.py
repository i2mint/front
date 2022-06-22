from abc import ABC
from copy import copy
from typing import Any, Callable, Iterable
from meshed import DAG
from front.elements import (
    NamedContainerBase,
    ElementTreeMakerBase,
    VIEW_CONTAINER,
    SECTION_CONTAINER,
    EXEC_SECTION_CONTAINER,
    FLOAT_INPUT_COMPONENT,
    TEXT_INPUT_COMPONENT,
    INT_INPUT_COMPONENT,
    GRAPH_COMPONENT,
)
from front.elements.element_flags import TEXT_OUTPUT_COMPONENT
from front.spec_maker import SpecMaker
from front.types import FrontApp, FrontSpec, Map
from front.util import obj_name


def dflt_trans(objs):
    def gen_trans_obj():
        for obj in objs:
            trans_obj = (
                DAG([obj]) if callable(obj) and not isinstance(obj, DAG) else copy(obj)
            )
            trans_obj.__name__ = obj_name(obj)
            yield trans_obj

    return list(gen_trans_obj())


def dflt_convention():
    return {
        'app': {'title': 'My Front Application'},
        'obj': {'trans': dflt_trans},
        'rendering': {
            DAG: {
                'container': VIEW_CONTAINER,
                'execution': {
                    'container': EXEC_SECTION_CONTAINER,
                    'name': 'Execution',
                    'inputs': {
                        int: {'component': INT_INPUT_COMPONENT,},
                        float: {
                            'component': FLOAT_INPUT_COMPONENT,
                            'format': '%.2f',
                            'step': 0.01,
                        },
                        Any: {'component': TEXT_INPUT_COMPONENT,},
                    },
                    # 'output': {
                    #     Any: {'component': TEXT_OUTPUT_COMPONENT,}
                    # }
                },
                'graph': {
                    'container': SECTION_CONTAINER,
                    'name': 'Flow',
                    'component': GRAPH_COMPONENT,
                    'display': True,
                    'display_for_single_node': False,
                },
            },
        },
    }


class AppMakerBase(ABC):
    def __init__(
        self,
        element_tree_maker_factory: Callable,
        spec_maker_factory: Callable = SpecMaker,
    ):
        self.spec_maker: SpecMaker = spec_maker_factory()
        self.el_tree_maker: ElementTreeMakerBase = element_tree_maker_factory()

    def mk_app(
        self, objs: Iterable[Any], config: Map = None, convention: Map = None
    ) -> FrontApp:
        element_tree, app_spec = self._element_tree_and_spec(objs, config, convention)
        return self._mk_app(element_tree, app_spec)

    # TODO: Find a way so this method does not do two things. Maybe consider the
    # element tree to be part of the spec object.
    def _element_tree_and_spec(
        self, objs: Iterable[Any], config: Map = None, convention: Map = None
    ):
        convention = convention or dflt_convention
        spec = self._mk_spec(config, convention)
        front_objs = self._prepare_objs(objs, spec.obj_spec)
        element_tree = self._mk_element_tree(front_objs, spec.rendering_spec)
        return element_tree, spec.app_spec

    def _mk_spec(self, config: Map, convention: Map) -> FrontSpec:
        return self.spec_maker.mk_spec(config, convention)

    def _prepare_objs(self, objs: Iterable[Any], obj_spec: dict) -> Iterable[Any]:
        def validate_obj(obj):
            if not isinstance(obj, Callable):
                raise NotImplementedError(
                    'Only objects of type Callable are supported for now.'
                )

        for obj in objs:
            validate_obj(obj)

        trans_func = obj_spec['trans']
        return trans_func(objs)

    def _mk_element_tree(
        self, objs: Iterable[Any], rendering_spec: dict
    ) -> NamedContainerBase:
        return self.el_tree_maker.mk_tree(objs, rendering_spec)

    def _mk_app(self, element_tree: NamedContainerBase, app_specs: dict) -> FrontApp:
        element_tree.name = app_specs['title']
        return element_tree.render
