from abc import ABC, abstractmethod
from inspect import Parameter, _empty
from typing import Callable, Iterable
from enum import IntFlag


class ContainerFlag(IntFlag):
    APP = (0,)
    VIEW = (1,)


class InputComponentFlag(IntFlag):
    TEXT = (1,)
    INT = (2,)
    FLOAT = (4,)
    FLOAT_SLIDER = (8,)


# class OutputComponentFlag(IntFlag):
#     TEXT = 1,
#     NUMBER = 2,


# ComponentFlag = Union[InputComponentFlag, OutputComponentFlag]
# ElementFlag = Union[ContainerFlag, ComponentFlag]


class FrontElementBase(ABC):
    @abstractmethod
    def render(self):
        # raise NotImplementedError('This method needs to be implemented in subclasses.')
        pass


class FrontContainerBase(FrontElementBase):
    children: Iterable[FrontElementBase]

    def __init__(self, children: Iterable[FrontElementBase] = None):
        self.children = children or []


class FrontComponentBase(FrontElementBase):
    pass


class AppBase(FrontContainerBase):
    title: str = None


class ParamInputBase(FrontComponentBase):
    def __init__(self, param: Parameter):
        super().__init__()
        self.param = param
        self.label = param.name
        self.init_value = param.default if param.default != _empty else None


class FuncViewBase(FrontContainerBase):
    def __init__(self, func: Callable, children: Iterable[ParamInputBase] = None):
        super().__init__(children)
        self.func = func
        self.name = func.__name__ or 'Front Func View'


class TextInputBase(ParamInputBase):
    def __init__(self, param: Parameter) -> None:
        super().__init__(param)
        self.init_value = str(self.init_value) if self.init_value is not None else ''


class NumberInputBase(ParamInputBase):
    def __init__(
        self, param: Parameter, min_value=None, max_value=None, format: str = None
    ):
        super().__init__(param)
        self.min_value = min_value
        self.max_value = max_value
        self.format = format


class IntInputBase(NumberInputBase):
    def __init__(
        self,
        param: Parameter,
        min_value: int = None,
        max_value: int = None,
        format: str = None,
    ):
        super().__init__(param, min_value, max_value, format)
        self.init_value = int(self.init_value) if self.init_value is not None else 0


class FloatInputBase(NumberInputBase):
    def __init__(
        self,
        param: Parameter,
        min_value: float = None,
        max_value: float = None,
        format: str = None,
        step: float = None,
    ):
        super().__init__(param, min_value, max_value, format)
        self.init_value = float(self.init_value) if self.init_value is not None else 0.0
        self.step = step
