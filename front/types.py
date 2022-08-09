from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Union

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


# @dataclass
# class BoundDataValue:
#     id: str
#     state: Mapping

#     def __get__(self, instance, owner):
#         print('__get__', self.id)
#         if self.id in self.state:
#             return self.state[self.id]

#     def __set__(self, instance, value):
#         print('__set__', self.id)
#         self.state[self.id] = value


@dataclass
class BoundData:
    id: str
    state: Mapping

    # def __init__(self, id, state):
    #     setattr(type(self), id, BoundDataValue(id, state))
    #     self.id = id

    @property
    def value(self):
        if self.id in self.state:
            return self.state[self.id]

    @value.setter
    def value(self, v):
        self.state[self.id] = v
