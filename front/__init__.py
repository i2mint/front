"""Dispatching python functions as webservices, docker containers, and GUIs"""


from contextlib import suppress

# TODO: Find a better way to do this (plugin) thing
with suppress(ModuleNotFoundError, ImportError):
    from streamlitfront import page_funcs
    from streamlitfront import session_state
    from streamlitfront import base
    from streamlitfront import util
    from streamlitfront import *
    from warnings import warn
    warn("Moved to seperate streamlitfront package", DeprecationWarning)
