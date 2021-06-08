"""Utils"""


def incremental_str_maker(str_format='{:03.f}'):
    """Make a function that will produce a (incrementally) new string at every call."""
    i = 0

    def mk_next_str():
        nonlocal i
        i += 1
        return str_format.format(i)

    return mk_next_str


unnamed_page = incremental_str_maker(str_format='UnnamedPage{:03.0f}')


def func_name(func):
    """The func.__name__ of a callable func, or makes and returns one if that fails.
    To make one, it calls unamed_func_name which produces incremental names to reduce the chances of clashing"""
    try:
        name = func.__name__
        if name == '<lambda>':
            return unnamed_page()
        return name
    except AttributeError:
        return unnamed_page()
