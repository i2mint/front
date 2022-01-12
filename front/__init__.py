"""Dispatching python functions as webservices, docker containers, and GUIs

Consider these three functions:

>>> def foo(a: int = 0, b: int = 0, c=0):
...     'This is foo. It computes something'
...     return (a * b) + c
>>> def bar(x, greeting='hello'):
...     'bar greets its input'
...     return f'{greeting} {x}'
>>> def confuser(a: int = 0, x: float = 3.14):
...     return (a ** 2) * x

The objective here is to be able to do this:

>>> app = dispatch_funcs([foo, bar, confuser], ...)  # doctest: +SKIP

getting a deployable app that allows the user to operate with these three wonderful
functions. The ellipses (`...`) are there to indicate that we may want to specify
the kind of app we want (web-service, GUI, CLI...) as well as particular configurations
for the latter.

"""


from contextlib import suppress

# TODO: Find a better way to do this (plugin) thing
with suppress(ModuleNotFoundError, ImportError):
    from streamlitfront import page_funcs
    from streamlitfront import session_state
    from streamlitfront import base
    from streamlitfront import util
    from streamlitfront import *
    from warnings import warn

    warn('Moved to seperate streamlitfront package', DeprecationWarning)
