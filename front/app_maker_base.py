from abc import ABC
from typing import Any, Callable, Iterable
from front.elements import (
    COMPONENT_FLOAT,
    COMPONENT_TEXT,
    AppBase,
    COMPONENT_INT,
    CONTAINER_VIEW,
    ElementTreeMakerBase,
)
from front.spec_maker import SpecMaker
from front.types import FrontApp, FrontSpec, Map
from front.elements import AppBase, CONTAINER_VIEW
from front.util import dflt_name_trans


def dflt_trans(objs):
    for obj in objs:
        obj.__name__ = dflt_name_trans(obj)

    return objs


def dflt_convention():
    return {
        'app': {'title': 'My Front Application'},
        'obj': {'trans': dflt_trans},
        'rendering': {
            Callable: {
                'container': CONTAINER_VIEW,
                'inputs': {
                    int: {'component': COMPONENT_INT,},
                    float: {
                        'component': COMPONENT_FLOAT,
                        'format': '%.2f',
                        'step': 0.01,
                    },
                    Any: {'component': COMPONENT_TEXT,},
                },
            },
        },
    }


class AppMakerBase(ABC):
    """
    Base class which 
    """

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

    def _mk_element_tree(self, objs: Iterable[Any], rendering_spec: dict) -> AppBase:
        return self.el_tree_maker.mk_tree(objs, rendering_spec)

    def _mk_app(self, element_tree: AppBase, app_specs: dict) -> FrontApp:
        element_tree.title = app_specs['title']
        return element_tree.render
