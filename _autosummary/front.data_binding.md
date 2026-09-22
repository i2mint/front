# front.data_binding

Data-binding primitives that connect front element values to a backing state store.

A [`BoundData`](#front.data_binding.BoundData) wraps a keyed slot in a [`State`](front.state.md#front.state.State) so an
element can read and write its current value through a single object. The
`ValueNotSet` / `Empty` sentinels distinguish “no value yet” from a
deliberate empty value.

### Classes

| [`Binder`](#front.data_binding.Binder)(front_state)   | Expose keys of `front_state` as attributes (or items) that are `BoundData` handles.   |
|------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| [`BoundData`](#front.data_binding.BoundData)(id, state)  | A read/write handle on one key (`id`) of a state mapping.                             |

### *class* front.data_binding.Binder(front_state)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Expose keys of `front_state` as attributes (or items) that are `BoundData` handles.

Reading an unknown attribute creates a handle for that key (without writing to
the state); assigning to it creates the handle and writes the value.

```pycon
>>> state = {}
>>> b = Binder(state)
>>> b.foo.get()
ValueNotSet
>>> b.foo = 42
>>> b.foo(), state
(42, {'foo': 42})
>>> b['bar'] = 'hi'
>>> state
{'foo': 42, 'bar': 'hi'}
```

#### SEE ALSO
`front.state.mk_binder`: a descriptor-based variant with an allow-list of names.

#### bound_data_factory

alias of [`BoundData`](#front.data_binding.BoundData)

### *class* front.data_binding.BoundData(id, state)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A read/write handle on one key (`id`) of a state mapping.

`get` returns `ValueNotSet` while the key is absent; `set` writes through
to the state. Calling the instance is the same as `get`.

```pycon
>>> state = {}
>>> bound = BoundData('x', state)
>>> bound.get()
ValueNotSet
>>> bound.set(3)
>>> bound(), state
(3, {'x': 3})
```

#### SEE ALSO
`Binder`: makes `BoundData` handles on demand, as attributes.

#### get()

Return the value stored under `id`, or `ValueNotSet`.

#### set(value)

Write `value` under `id` in the state.
