# front.spec_maker_base

Base classes and conventions for building a [`FrontSpec`](front.types.html.md#front.types.FrontSpec) from a configuration.

A spec maker is the “short language → long language” compiler of front: it
consumes a user configuration plus a convention (defaults) and emits the
nested `app` / `obj` / `rendering` specification consumed by
[`AppMaker`](front.app_maker.html.md#front.app_maker.AppMaker).

### Classes

| [`SpecMakerBase`](#front.spec_maker_base.SpecMakerBase)()   | Compile a user configuration (short language) into a `FrontSpec` (long language).   |
|--------------------------------------------------------------------|-------------------------------------------------------------------------------------|

### *class* front.spec_maker_base.SpecMakerBase

Bases: [`ABC`](https://docs.python.org/3/library/abc.html#abc.ABC)

Compile a user configuration (short language) into a `FrontSpec` (long language).

The configuration is merged over a convention (the defaults), then the
class-keyed entries of the rendering specification are completed along the
class hierarchy, so that a spec for a subclass inherits the spec of its bases.

To do so, the “mk_spec” method first merges the configuration with the convention,
then does the following for the rendering specification:
Let’s consider we have three classes A, B and C with C extends B and B extends A
(A <- B <- C). If the rendering configuration contains the following:

```default
{
    A: {
        'a': {...}
    },
    B: {
        'b': {...}
    },
    C: {
        'c': {...}
    },
}
```

The resulting rendering specification will be:

```default
{
    A: {
        'a': {...}
    },
    B: {
        'a': {...},
        'b': {...}
    },
    C: {
        'a': {...},
        'b': {...},
        'c': {...}
    },
}
```

This abstract class needs to be overloaded in every concrete front framework with
a concrete implementation for the “_dflt_convention” property, which will return
the convention after injecting the concrete element factories in it.

```pycon
>>> from front import APP_KEY, OBJ_KEY, RENDERING_KEY
>>> from front.util import dflt_trans
>>> class A: pass
>>> class B(A): pass
>>> class C(B): pass
>>> class SpecMaker(SpecMakerBase):
...     @property
...     def _dflt_convention(self):
...         return {
...             APP_KEY: {'title': 'Untitled'},
...             OBJ_KEY: {'trans': dflt_trans},
...             RENDERING_KEY: {A: {'a': 1}, B: {'b': 2}, C: {'c': 3}},
...         }
>>> spec = SpecMaker().mk_spec({APP_KEY: {'title': 'Demo'}})
>>> spec.app_spec
{'title': 'Demo'}
>>> spec.rendering_spec[C]
{'a': 1, 'b': 2, 'c': 3}
>>> spec.rendering_spec[B]
{'a': 1, 'b': 2}
```

#### SEE ALSO
`front.app_maker.AppMaker`: consumes the spec this class produces.
`front.util.deep_merge`: the merge used for config over convention.

#### mk_spec(config, convention=None)

Merge `config` over `convention` and complete class-keyed rendering specs.

* **Parameters:**
  * **config** (`Union`[[`None`](https://docs.python.org/3/builtins/constants.html#None), [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping), [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[], [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)]]) – The user configuration: a mapping, a callable returning one,
    or None (empty).
  * **convention** (`Union`[[`None`](https://docs.python.org/3/builtins/constants.html#None), [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping), [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[], [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)]]) – The defaults. If None, `self._dflt_convention` is used.
* **Return type:**
  [`FrontSpec`](front.types.html.md#front.types.FrontSpec)
* **Returns:**
  A `FrontSpec` with `app_spec`, `obj_spec` and `rendering_spec`.
