from abc import ABC
from typing import Any, Callable, Iterable
from front.elements import ElementTreeMaker
from front.elements.elements import FrontContainerBase
from front.spec_maker_base import SpecMakerBase
from front.types import FrontApp, Map


class AppMaker:
    """Main class of front, doing the following:
    1. Consume the configuration (short language) to produce a specification object
    (long language) using the provided spec maker. The specification is a nested
    structure which contains 3 sub-specification objects: "obj", "rendering" and "app".
    2. Transform the input objects using the "trans" function from the "obj"
    specification (uses front.util.dflt_trans by default).
    3. Build a composite tree of Front elements based on the "rendering" specification.
    4. Build an app from the composite tree and "app" specification.
    """

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
        """Entry point of the AppMaker class to make a Front application.

        :param objs: The objects that the user of the resulting
            application will be interacting with.
        :param config: The configuration of the resulting application.
        :param convention: The convention used to complete the configuration by
            providing default values for everything that is not specified in the
            configuration.
        """
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
        return element_tree
