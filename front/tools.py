"""Tools using front, or useful when using front"""

from typing import Sequence, KT, VT, Callable, Iterable, Sized, Container
from dol import KvReader
from dataclasses import dataclass


class SizedIterableContainer(Sized, Iterable, Container):
    """An object with a __len__, __iter__, and __contains__ method"""


@dataclass
class ValuesStore(KvReader):
    """A mapping view of a sequence where the items of the sequence are both
    keys and values of the mapping

    >>> vs = ValuesStore([1, 2, 3])
    >>> list(vs)
    [1, 2, 3]
    >>> vs[1]
    1
    >>> len(vs)
    3
    >>> 4 in vs
    False

    """

    seq: SizedIterableContainer
    # TODO: Should we generalize using val_to_key and key_to_val?
    # val_to_key: Callable[[VT], KT] = identity
    # key_to_val: Callable[[KT], VT] = identity

    def __iter__(self) -> Iterable[KT]:
        yield from self.seq

    def __getitem__(self, k: KT) -> VT:
        if k in self:
            return k
        else:
            raise KeyError(f"This key wasn't found: {k}")

    def __len__(self) -> int:
        return len(self.seq)

    def __contains__(self, k: KT) -> bool:
        return k in self.seq


@dataclass
class FactoryFedSizedIterableContainer(SizedIterableContainer):
    iterable_factory: Callable[[], Iterable]

    def __iter__(self):
        yield from self.iterable_factory()

    def __len__(self):
        return len(list(self.iterable_factory()))

    def __contains__(self, k):
        return any(x == k for x in self.iterable_factory())
