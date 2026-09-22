# front.app_maker

The `AppMaker` orchestrator that turns a configuration into a front app.

Consumes a short-language configuration plus a convention, compiles it into a
nested [`FrontSpec`](front.types.md#front.types.FrontSpec) (the long language) via a spec maker,
builds the composite tree of front elements, and assembles the runnable app.

### Classes

| [`AppMaker`](#front.app_maker.AppMaker)(spec_maker_factory[, ...])   | Orchestrator that turns objects plus a configuration into a runnable front app.   |
|----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|

### *class* front.app_maker.AppMaker(spec_maker_factory, element_tree_maker_factory=<class 'front.elements.tree_maker_base.ElementTreeMaker'>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Orchestrator that turns objects plus a configuration into a runnable front app.

Main class of front, doing the following:

1. Consume the configuration (short language) to produce a specification object
   (long language) using the provided spec maker. The specification is a nested
   structure which contains 3 sub-specification objects: “obj”, “rendering” and “app”.
2. Transform the input objects using the “trans” function from the “obj”
   specification (uses front.util.dflt_trans by default).
3. Build a composite tree of Front elements based on the “rendering” specification.
4. Build an app from the composite tree and “app” specification.

A concrete front framework subclasses `SpecMakerBase` (to supply its default
convention, including the concrete element classes) and hands that class to
`AppMaker`. Below, a minimal in-memory framework whose “app” is a container
that renders each function’s docstring:

```pycon
>>> from collections.abc import Callable
>>> from front import SpecMakerBase, APP_KEY, OBJ_KEY, RENDERING_KEY, ELEMENT_KEY
>>> from front.elements import FrontContainerBase, FrontComponentBase
>>> from front.util import dflt_trans
>>>
>>> class App(FrontContainerBase):
...     def render(self):
...         return {child.name: child() for child in self.children}
>>> class Doc(FrontComponentBase):
...     def render(self):
...         return self.obj.__doc__
>>> class SpecMaker(SpecMakerBase):
...     @property
...     def _dflt_convention(self):
...         return {
...             APP_KEY: {'title': 'Untitled'},
...             OBJ_KEY: {'trans': dflt_trans},
...             RENDERING_KEY: {ELEMENT_KEY: App, Callable: {ELEMENT_KEY: Doc}},
...         }
>>> def foo(a, b):
...     "Adds a and b."
...     return a + b
>>> app_maker = AppMaker(spec_maker_factory=SpecMaker)
>>> app = app_maker.mk_app([foo], config={APP_KEY: {'title': 'My App'}})
>>> app.name
'My App'
>>> app()
{'foo': 'Adds a and b.'}
```

Anything the config doesn’t say comes from the convention:

```pycon
>>> app_maker.mk_app([foo]).name
'Untitled'
```

#### SEE ALSO
`front.spec_maker_base.SpecMakerBase`: compiles config + convention into the spec.
`front.elements.ElementTreeMaker`: builds the element tree from the rendering spec.

#### mk_app(objs, config=None, convention=None)

Make a front application exposing `objs`: the entry point of `AppMaker`.

* **Parameters:**
  * **objs** ([`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]) – The objects that the user of the resulting
    application will be interacting with. Only callables are supported for now.
  * **config** (`Union`[[`None`](https://docs.python.org/3/builtins/constants.html#None), [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping), [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[], [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)]]) – The configuration of the resulting application.
  * **convention** (`Union`[[`None`](https://docs.python.org/3/builtins/constants.html#None), [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping), [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[], [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)]]) – The convention used to complete the configuration by
    providing default values for everything that is not specified in the
    configuration. Defaults to the spec maker’s `_dflt_convention`.
* **Return type:**
  [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)
* **Returns:**
  The root element of the app tree, named after the app’s title.
* **Raises:**
  [**NotImplementedError**](https://docs.python.org/3/builtins/exceptions.html#NotImplementedError) – If an object in `objs` is not callable.
