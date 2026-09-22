# front

Dispatching python functions as webservices, docker containers, and GUIs.

`front` is the core library that concrete UI frameworks (e.g. `streamlitfront`)
build on: it compiles a configuration into a specification (`SpecMakerBase`),
builds a tree of UI elements from it (`ElementTreeMaker`) and assembles the app
(`AppMaker`). `Crudifier` and `prepare_for_crude_dispatch` make functions
with complex arguments operable through string keys into stores.

Consider these three functions:

```pycon
>>> def foo(a: int = 0, b: int = 0, c=0):
...     'This is foo. It computes something'
...     return (a * b) + c
>>> def bar(x, greeting='hello'):
...     'bar greets its input'
...     return f'{greeting} {x}'
>>> def confuser(a: int = 0, x: float = 3.14):
...     return (a ** 2) * x
```

The objective here is to be able to do this:

```pycon
>>> app = dispatch_funcs([foo, bar, confuser], ...)
```

getting a deployable app that allows the user to operate with these three wonderful
functions. The ellipses (`...`) are there to indicate that we may want to specify
the kind of app we want (web-service, GUI, CLI…) as well as particular configurations
for the latter.

### Modules

| [`app_maker`](front.app_maker.md#module-front.app_maker)             | The `AppMaker` orchestrator that turns a configuration into a front app.                                                                           |
|-----------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| [`base`](front.base.md#module-front.base)                       | Base functions for front dispatching: `prepare_for_dispatch` chains the wrappers a UI needs.                                                       |
| [`crude`](front.crude.md#module-front.crude)                     | Crudify functions: let complex arguments be specified by string keys into stores.                                                                  |
| [`dag`](front.dag.md#module-front.dag)                         | Crudify the variable nodes of a `meshed` DAG.                                                                                                      |
| [`data_binding`](front.data_binding.md#module-front.data_binding)       | Data-binding primitives that connect front element values to a backing state store.                                                                |
| [`elements`](front.elements.md#module-front.elements)               | Front UI elements: bases, tree maker, and component implementer helpers.                                                                           |
| [`py2pydantic`](front.py2pydantic.md#module-front.py2pydantic)         | Bridge between plain Python functions and pydantic v2 models.                                                                                      |
| [`spec_maker_base`](front.spec_maker_base.md#module-front.spec_maker_base) | Base classes and conventions for building a [`FrontSpec`](front.types.md#front.types.FrontSpec) from a configuration. |
| [`state`](front.state.md#module-front.state)                     | Stateful storage protocols and `Forbidden` errors used by front data bindings.                                                                     |
| [`tools`](front.tools.md#module-front.tools)                     | Tools using front, or useful when using front.                                                                                                     |
| [`types`](front.types.md#module-front.types)                     | Type aliases and lightweight dataclasses shared across front modules.                                                                              |
| [`util`](front.util.md#module-front.util)                       | Signature and mapping utilities shared by the front modules.                                                                                       |
