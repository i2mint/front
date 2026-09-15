# front.state

Stateful storage protocols and `Forbidden` errors used by front data bindings.

Defines the [`State`](#front.state.State) wrapper and the `GetterSetter` / `StateType`
protocols an app’s backing store must satisfy, plus a small hierarchy of
`Forbidden*` exceptions raised when a write breaks the configured policy.

### Functions

| [`mk_binder`](#front.state.mk_binder)([state, allowed_ids, ...])   | Make a `Binder` class (or instance) whose attributes read and write a state mapping.   |
|-----------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|

### Classes

| [`BoundVal`](#front.state.BoundVal)(key, \*[, value_not_set])     | Descriptor reading and writing `key` in the owner's `_state` mapping.        |
|-----------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| [`DFLT_BOUND_VAL_FACTORY`](#front.state.DFLT_BOUND_VAL_FACTORY)                 |                                                                              |
| [`GetterSetter`](#front.state.GetterSetter)(\*args, \*\*kwargs)       | The type of an object `obj` supporting `v = obj[k]` and `obj[k] = v`.        |
| [`HasState`](#front.state.HasState)(\*args, \*\*kwargs)           | An object with a `_state` mutable mapping, as `BoundVal` descriptors expect. |
| [`IsInstanceOf`](#front.state.IsInstanceOf)(class_or_tuple)           | A picklable `isinstance` predicate: `IsInstanceOf(int)(3)` is True.          |
| [`State`](#front.state.State)(state[, condition_for_key, ...]) | A write-policing wrapper around a key-value `state` (any `GetterSetter`).    |

### Exceptions

| [`ConditionNotMet`](#front.state.ConditionNotMet)    | Raised when a value doesn't meet the condition set for its key.          |
|---------------------------------------------------------------------|--------------------------------------------------------------------------|
| [`Forbidden`](#front.state.Forbidden)          | Base of the errors raised when an operation is not allowed.              |
| [`ForbiddenOverwrite`](#front.state.ForbiddenOverwrite) | Raised when writing a different value to an existing key is not allowed. |
| [`ForbiddenWrite`](#front.state.ForbiddenWrite)     | Raised when writing to a key is not allowed.                             |

### *class* front.state.BoundVal(key, , value_not_set=ValueNotSet)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Descriptor reading and writing `key` in the owner’s `_state` mapping.

Reading returns `value_not_set` (`ValueNotSet` by default) while the key
is absent.

```pycon
>>> class Obj:
...     _state = {}
...     x = BoundVal('x')
>>> obj = Obj()
>>> obj.x
ValueNotSet
>>> obj.x = 5
>>> obj.x, Obj._state
(5, {'x': 5})
>>> Obj.x
BoundVal('x')
```

### *exception* front.state.ConditionNotMet

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

Raised when a value doesn’t meet the condition set for its key.

### front.state.DFLT_BOUND_VAL_FACTORY

alias of [`BoundVal`](#front.state.BoundVal)

### *exception* front.state.Forbidden

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

Base of the errors raised when an operation is not allowed.

### *exception* front.state.ForbiddenOverwrite

Bases: [`Forbidden`](#front.state.Forbidden)

Raised when writing a different value to an existing key is not allowed.

### *exception* front.state.ForbiddenWrite

Bases: [`Forbidden`](#front.state.Forbidden)

Raised when writing to a key is not allowed.

### *class* front.state.GetterSetter(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

The type of an object `obj` supporting `v = obj[k]` and `obj[k] = v`.

### *class* front.state.HasState(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

An object with a `_state` mutable mapping, as `BoundVal` descriptors expect.

### *class* front.state.IsInstanceOf(class_or_tuple)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A picklable `isinstance` predicate: `IsInstanceOf(int)(3)` is True.

### *class* front.state.State(state, condition_for_key=(), forbidden_writes=(), forbidden_overwrites=())

Bases: [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)

A write-policing wrapper around a key-value `state` (any `GetterSetter`).

Reads and the other `MutableMapping` operations forward to `state`. Writes
are checked first: keys in `forbidden_writes` can never be written; keys in
`forbidden_overwrites` can be written once (re-writing the same value is
allowed); a key in `condition_for_key` only accepts values for which its
predicate is true (a type there means `isinstance`).

```pycon
>>> state = State(
...     state={},
...     forbidden_writes={'foo'},
...     forbidden_overwrites={'apple'},
...     condition_for_key={'apple': list, 'carrot': lambda x: x > 10},
... )
>>> state['apple'] = [4, 2]
>>> state['apple'] = [4, 2]  # same value again: fine
>>> state['apple'] = [1]
Traceback (most recent call last):
...
front.state.ForbiddenOverwrite: Not allowed to write under this key more than once: apple
>>> state['foo'] = 1
Traceback (most recent call last):
...
front.state.ForbiddenWrite: Not allowed to write on foo
>>> state['carrot'] = 10
Traceback (most recent call last):
...
front.state.ConditionNotMet: The value for the carrot key must satisfy condition <function <lambda> at 0x...>
>>> state['carrot'] = 11
>>> dict(state)
{'apple': [4, 2], 'carrot': 11}
```

* **Raises:**
  * [**ForbiddenWrite**](#front.state.ForbiddenWrite) – On writing a key of `forbidden_writes`.
  * [**ForbiddenOverwrite**](#front.state.ForbiddenOverwrite) – On writing a different value to an existing key of
    `forbidden_overwrites`.
  * [**ConditionNotMet**](#front.state.ConditionNotMet) – On writing a value that fails the key’s condition.

#### get(k, default=None)

Return `state[k]` if `k` is in the state, else `default`.

### front.state.mk_binder(state=None, allowed_ids=None, bound_val_factory=<class 'front.state.BoundVal'>)

Make a `Binder` class (or instance) whose attributes read and write a state mapping.

Returns a class when `state` is None, and an instance bound to `state`
otherwise. With `allowed_ids`, only those names are bound (as `bound_val_factory`
descriptors); without, any identifier is bound on first access.

```pycon
>>> Binder = mk_binder()
>>> d = dict()
>>> b = Binder(d)
```

If I ask for `b.foo` (or any valid python identifier I want) it’ll be inserted
as an “descriptor” attribute of `Binder`, but it’s  value will be special value
`ValueNotSet`.

```pycon
>>> b.foo
ValueNotSet
>>> 'foo' in dir(Binder)
True
```

Let’s set the value of `foo`:

```pycon
>>> b.foo = 42
>>> b.foo
42
```

So `b.foo` is now set, but the real point is that this assignment was “registered”
in the state we give the `Binder`:

```pycon
>>> d
{'foo': 42}
```

Wanna see that again?

```pycon
>>> b.foo = "I'm bound"
>>> b.foo
"I'm bound"
>>> d
{'foo': "I'm bound"}
```

And same with `b.bar`:

```pycon
>>> b.bar
ValueNotSet
>>> b.bar = "me too"
>>> b.bar
'me too'
>>> d
{'foo': "I'm bound", 'bar': 'me too'}
```

A `Binder` will also have some useful mapping methods that are linked to the
underlying `state`.

```pycon
>>> Binder = mk_binder(allowed_ids=['the', 'variables', 'I', 'want'])
>>> state = dict()
>>> b = Binder(state)
>>> list(b)
[]
>>> b.want  # I see a want, but no value is set
ValueNotSet
>>> list(b)  # list still gives me nothing
[]
>>> b.want = 42  # but if I set a value for want
>>> list(b)  # I see want in the list
['want']
>>> 'want' in b  # I can do this too
True
>>> 'not_in_there' in b
False
>>> 'variables' in b  # 'variables' not "there" because not set
False
```
