# front.elements.tree_maker_base

`ElementTreeMaker`: builds the composite tree of front elements from a rendering spec.

The tree is then walked by [`AppMaker`](front.app_maker.html.md#front.app_maker.AppMaker) to produce the
runnable app. Concrete frontends typically don’t override this — they supply
their own element classes via the rendering specification.

### Classes

| [`ElementTreeMaker`](#front.elements.tree_maker_base.ElementTreeMaker)()   | Build the composite tree of front elements from a compiled rendering spec.   |
|-----------------------------------------------------------------------|------------------------------------------------------------------------------|

### *class* front.elements.tree_maker_base.ElementTreeMaker

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Build the composite tree of front elements from a compiled rendering spec.

The rendering specification maps `ELEMENT_KEY` to the root container factory,
and types (or names) of the objects to render to their element specs. The
resulting tree is rendered by calling its root, which renders each element
recursively.

```pycon
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
```

#### SEE ALSO
`front.app_maker.AppMaker`: calls `mk_tree` with the compiled spec.

#### mk_tree(front_objs, rendering_spec)

Build the composite tree: the entry point of `ElementTreeMaker`.

* **Parameters:**
  * **front_objs** ([`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]) – The objects to render after transformation (see AppMaker).
  * **rendering_spec** ([`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)) – The rendering spec of the application, compiled from
    the given configuration.
    This nested object contains information on how an object should be rendered
    based on its type (general spec that can be reused for several objects) or
    its name (specific spec for a single object). Both specs can be used for a
    single objects. In that case, the spec that will be used for this object
    will be a combination between those two specs (any value in the specific
    spec overwrites the value in the general spec for any key that they could
    have in common).
* **Return type:**
  [`FrontContainerBase`](front.elements.elements.html.md#front.elements.elements.FrontContainerBase)
* **Returns:**
  The root container, with one child element per object.
* **Raises:**
  [**KeyError**](https://docs.python.org/3/builtins/exceptions.html#KeyError) – If `rendering_spec` has no `ELEMENT_KEY` (root factory).
