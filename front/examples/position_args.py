from typing import Iterable
import os


def add_ints(*nums_to_add: Iterable[int]):
    return sum(nums_to_add)


def add_floats(*nums_to_add: Iterable[float]):
    return sum(nums_to_add)


def add_strs(*strs_to_add: Iterable[str]):
    return ' '.join(strs_to_add)


def add_bools(*bools_to_add: Iterable[bool]):
    return sum(list(map(int, bools_to_add)))


funcs = [add_ints, add_floats, add_strs, add_bools]

if __name__ == '__main__':
    from front.base import dispatch_funcs
    from front.page_funcs import PositionalArgsPageFunc

    print('file: {}'.format(os.path.realpath(__file__)))

    app = dispatch_funcs(funcs, configs={'page_factory': PositionalArgsPageFunc})

    app()
