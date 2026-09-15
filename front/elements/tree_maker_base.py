"""``ElementTreeMaker``: builds the composite tree of front elements from a rendering spec.

The tree is then walked by :class:`~front.app_maker.AppMaker` to produce the
runnable app. Concrete frontends typically don't override this — they supply
their own element classes via the rendering specification.
"""

from abc import ABC, abstractclassmethod
from typing import Any
from collections.abc import Iterable
from front.elements.elements import (
    ELEMENT_KEY,
    FrontContainerBase,
)
from front.util import deep_merge


class ElementTreeMaker:
    """Build the composite tree of front elements from a compiled rendering spec.

    The rendering specification maps ``ELEMENT_KEY`` to the root container factory,
    and types (or names) of the objects to render to their element specs. The
    resulting tree is rendered by calling its root, which renders each element
    recursively.

    >>> from collections.abc import Callable
    >>> from front.elements import FrontContainerBase, FrontComponentBase, ELEMENT_KEY
    >>> class App(FrontContainerBase):
    ...     def render(self):
    ...         return {child.name: child() for child in self.children}
    >>> class Doc(FrontComponentBase):
    ...     def render(self):
    ...         return self.obj.__doc__
    >>> def foo(a, b):
    ...     "Adds a and b."
    ...     return a + b
    >>> rendering_spec = {ELEMENT_KEY: App, Callable: {ELEMENT_KEY: Doc}}
    >>> tree = ElementTreeMaker().mk_tree([foo], rendering_spec)
    >>> type(tree).__name__, [type(child).__name__ for child in tree.children]
    ('App', ['Doc'])
    >>> tree()
    {'foo': 'Adds a and b.'}

    See Also:
        ``front.app_maker.AppMaker``: calls ``mk_tree`` with the compiled spec.
    """

    def mk_tree(
        self, front_objs: Iterable[Any], rendering_spec: dict
    ) -> FrontContainerBase:
        """Build the composite tree: the entry point of ``ElementTreeMaker``.

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
        :return: The root container, with one child element per object.
        :raises KeyError: If ``rendering_spec`` has no ``ELEMENT_KEY`` (root factory).
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
                "No app element has been defined for this front application."
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
            obj_rendering_spec["obj"] = obj
            yield (obj_name, obj_rendering_spec)

    def _get_type_rendering_spec(self, spec: dict, obj):
        obj_type = type(obj)
        obj_type_spec = spec.get(obj_type)
        if obj_type_spec:
            return obj_type_spec
        if getattr(obj_type, "mro"):
            for t in obj_type.mro():
                type_spec = spec.get(t)
                if type_spec:
                    return type_spec
        for k, v in spec.items():
            if isinstance(obj, k):
                return v
        return {}
