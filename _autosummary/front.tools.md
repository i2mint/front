# front.tools

Tools using front, or useful when using front.

### Classes

| [`FactoryFedSizedIterableContainer`](#front.tools.FactoryFedSizedIterableContainer)(...)   | A sized iterable container over the items of `iterable_factory()`, re-called on every use.   |
|------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| [`SizedIterableContainer`](#front.tools.SizedIterableContainer)()                | An object with `__len__`, `__iter__` and `__contains__` methods.                             |
| [`ValuesStore`](#front.tools.ValuesStore)(seq)                        | A mapping view of a sequence where the items of the sequence are both keys and values.       |

### *class* front.tools.FactoryFedSizedIterableContainer(iterable_factory)

Bases: [`SizedIterableContainer`](#front.tools.SizedIterableContainer)

A sized iterable container over the items of `iterable_factory()`, re-called on every use.

```pycon
>>> c = FactoryFedSizedIterableContainer(lambda: range(3))
>>> list(c), len(c), 2 in c, 5 in c
([0, 1, 2], 3, True, False)
```

### *class* front.tools.SizedIterableContainer

Bases: [`Sized`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sized), [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable), [`Container`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Container)

An object with `__len__`, `__iter__` and `__contains__` methods.

### *class* front.tools.ValuesStore(seq)

Bases: `KvReader`

A mapping view of a sequence where the items of the sequence are both keys and values.

```pycon
>>> vs = ValuesStore([1, 2, 3])
>>> list(vs)
[1, 2, 3]
>>> vs[1]
1
>>> len(vs)
3
>>> 4 in vs
False
```
