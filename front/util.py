"""Utils"""

from i2.signatures import name_of_obj


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
    name = name_of_obj(func)
    if name is None or name == '<lambda>':
        return unnamed_page()
    return name


class Objdict(dict):
    """A dict, whose keys can be access as if they were attributes.
    >>> s = Objdict()
    Write it as you do with attributes or dict keys,
    get it as an attribute and a dict keys.
    >>> s.foo = 'bar'
    >>> assert s.foo == 'bar'
    >>> assert s['foo'] == 'bar'
    >>> s['hello'] = 'world'
    >>> assert s.hello == 'world'
    >>> assert s['hello'] == 'world'
    >>> hasattr(s, 'hello')
    True
    And you can still do dict stuff with it...
    >>> list(s)
    ['foo', 'hello']
    >>> list(s.items())
    [('foo', 'bar'), ('hello', 'world')]
    >>> s.get('key not there', 'nope')
    'nope'
    >>> s.clear()
    >>> assert len(s) == 0
    Note: You can use anything that's a valid dict key as a key
    >>> s['strings with space'] = 1
    >>> s[42] = 'meaning of life'
    >>> s[('tuples', 1, None)] = 'weird'
    >>> list(s)
    ['strings with space', 42, ('tuples', 1, None)]
    But obviously, the only ones you'll be able to access are those that are
    valid attribute names.
    """

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError('No such attribute: ' + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError('No such attribute: ' + name)


def build_factory(element_factory, kind, idx):
    factory = element_factory[f'{kind}_factory']
    kwargs = {'label': f'Enter {kind} {idx + 1}', 'key': idx}
    if element_factory[f'{kind}_type'] is int:
        kwargs['value'] = 0
    val = factory(**kwargs)
    return val
