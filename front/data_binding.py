from dataclasses import dataclass

from front.state import GetterSetter, State


NotFound = type('NotFound', (), {})()


class StateValueError(ValueError):
    'Raised when trying to add a forbidden value to the state.'


class BoundData:
    def __init__(self, id: str, state: GetterSetter):
        self.id = id
        self.state = State(state=state, forbidden_writes={NotFound})

    def get(self):
        return self.state.get(self.id, NotFound)

    def set(self, value):
        self.state[self.id] = value

    __call__ = get
