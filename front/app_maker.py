from abc import ABC
from typing import Any, Callable, Iterable
from front.elements import ElementTreeMaker
from front.elements.elements import FrontContainerBase
from front.spec_maker_base import SpecMakerBase
from front.types import FrontApp, Map


class AppMaker:
    def __init__(
        self,
        spec_maker_factory: Callable,
        element_tree_maker_factory: Callable = ElementTreeMaker,
    ):
        self.spec_maker: SpecMakerBase = spec_maker_factory()
        self.el_tree_maker: ElementTreeMaker = element_tree_maker_factory()

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
        spec = self.spec_maker.mk_spec(config, convention)
        front_objs = self._prepare_objs(objs, spec.obj_spec)
        element_tree = self.el_tree_maker.mk_tree(front_objs, spec.rendering_spec)
        return element_tree, spec.app_spec

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

    def _mk_app(self, element_tree: FrontContainerBase, app_specs: dict) -> FrontApp:
        element_tree.name = app_specs['title']
        return element_tree.render
