"""
Moved to seperate py2pydantic package
"""

from contextlib import suppress

with suppress(ModuleNotFoundError, ImportError):
    from opyratorfront.py2pydantic import *
    from warnings import warn

    warn('Moved to seperate py2pydantic package', DeprecationWarning)
