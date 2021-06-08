"""
Session state management
"""
import streamlit as st
from streamlit.hashing import _CodeHasher

try:
    # Before Streamlit 0.65
    from streamlit.ReportThread import get_report_ctx
    from streamlit.server.Server import Server
except ModuleNotFoundError:
    # After Streamlit 0.65
    from streamlit.report_thread import get_report_ctx
    from streamlit.server.server import Server


def display_state_values(state, key):
    st.write('Current value of ' + str(key) + ':', state[key])


class _SessionState:
    def __init__(self, session, hash_funcs):
        """Initialize SessionState instance."""
        self.__dict__['_state'] = {
            'data': {},
            'hash': None,
            'hasher': _CodeHasher(hash_funcs),
            'is_rerun': False,
            'session': session,
        }

    def __call__(self, **kwargs):
        """Initialize state data once."""
        for item, value in kwargs.items():
            if item not in self._state['data']:
                self._state['data'][item] = value

    def __getitem__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state['data'].get(item, None)

    def __getattr__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state['data'].get(item, None)

    def __setitem__(self, item, value):
        """Set state value."""
        self._state['data'][item] = value

    def __setattr__(self, item, value):
        """Set state value."""
        self._state['data'][item] = value

    def clear(self):
        """Clear session state and request a rerun."""
        self._state['data'].clear()
        self._state['session'].request_rerun()

    def has_valid(self, *k, is_valid=bool):
        """Checks that k exists and is valid.
        Validity can be specified by a function (default: bool).

        This says it all (sorta):

        >>> s = State(a=0, b=False, c=None, d='', e=1, f=True, h='hi')
        >>> list(filter(s.has_valid, list(s) + ['i', 'j']))
        ['e', 'f', 'h']

        But here's the slower presentation:

        >>> s = State(a=1)
        >>> s.has_valid('a')
        True
        >>> s['a'] = 0
        >>> s.has_valid('a')
        False

        'a' is 0, which evaluates to False,
        (since the default is_valid function is `bool`).
        But if we use another custom is_valid function, it becomes valid.

        >>> s.has_valid('a', is_valid=lambda x: x is not None)
        True

        But what ever your is_valid function, if a key doesn't exist,
        it won't be valid.

        >>> just_care_about_key_existence = lambda x: True
        >>> s.has_valid('b', is_valid=just_care_about_key_existence)
        False

        That's why the method is called HAS_valid.
        It needs to HAVE the key, and the value needs to be valid.

        You can also check the conjunctive validity of several keys.
        Conjunctive is a pedantic way of saying "and".

        >>> s = State(a=1, b=False, c=None)
        >>> s.has_valid('a', 'b')
        False
        >>> s['b'] = 2
        >>> s.has_valid('a', 'b')
        True

        Note that `is_valid` is a keyword-only argument.
        If you don't specify it as a keyword argument, it will think it's a
        key to validate. Silly it!

        >>> s.has_valid('a', 'b', 'c', just_care_about_key_existence)
        False
        >>> s.has_valid('a', 'b', 'c', is_valid=just_care_about_key_existence)
        True

        """
        # return all((key in self and is_valid(self[key])) for key in k)
        return all(
            (key in self and is_valid(self._state['data'].get(key, None))) for key in k
        )

    def sync(self):
        """Rerun the app with all state values up to date from the beginning to fix rollbacks."""

        # Ensure to rerun only once to avoid infinite loops
        # caused by a constantly changing state value at each run.
        #
        # Example: state.value += 1
        if self._state['is_rerun']:
            self._state['is_rerun'] = False

        elif self._state['hash'] is not None:
            if self._state['hash'] != self._state['hasher'].to_bytes(
                self._state['data'], None
            ):
                self._state['is_rerun'] = True
                self._state['session'].request_rerun()

        self._state['hash'] = self._state['hasher'].to_bytes(self._state['data'], None)


def _get_session():
    session_id = get_report_ctx().session_id
    session_info = Server.get_current()._get_session_info(session_id)

    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")

    return session_info.session


def _get_state(hash_funcs=None):
    session = _get_session()

    if not hasattr(session, '_custom_session_state'):
        session._custom_session_state = _SessionState(session, hash_funcs)

    return session._custom_session_state
