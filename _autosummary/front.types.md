# front.types

Type aliases and lightweight dataclasses shared across front modules.

Centralizes the names used in spec compilation (`Configuration`,
`Convention`, `Map`) and the structured [`FrontSpec`](#front.types.FrontSpec) consumed by
[`AppMaker`](front.app_maker.md#front.app_maker.AppMaker).

### Classes

| [`FrontSpec`](#front.types.FrontSpec)(app_spec, obj_spec, rendering_spec)   | The compiled specification: `app_spec`, `obj_spec` and `rendering_spec` dicts.   |
|--------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|

### *class* front.types.FrontSpec(app_spec, obj_spec, rendering_spec)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The compiled specification: `app_spec`, `obj_spec` and `rendering_spec` dicts.
