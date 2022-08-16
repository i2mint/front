from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Union, overload

Map = Union[None, Mapping, Callable[[], Mapping]]
Configuration = Mapping
Convention = Mapping
FrontElementName = Union[None, str, Callable[[Any], str]]


@dataclass
class FrontSpec:
    app_spec: dict
    obj_spec: dict
    rendering_spec: dict


FrontApp = Callable

NotFound = type('NotFound', (), {})()


class StateValueError(ValueError):
    'Raised when trying to add a forbidden value to the state.'


@dataclass
class BoundData:
    id: str
    state: Mapping

    def get(self):
        if self.id in self.state:
            return self.state[self.id]
        return NotFound

    def set(self, value):
        if value is NotFound:
            raise StateValueError('Cannot store NotFound in the state.')
        self.state[self.id] = value

    __call__ = get
