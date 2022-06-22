from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Iterable
from meshed import DAG


class FrontElementBase(ABC):
    @abstractmethod
    def render(self):
        # raise NotImplementedError('This method needs to be implemented in subclasses.')
        pass


class FrontContainerBase(FrontElementBase):
    children: Iterable[FrontElementBase]

    def __init__(self, children: Iterable[FrontElementBase] = None):
        self.children = children or []

    def _render_children(self):
        for child in self.children:
            child.render()


class FrontComponentBase(FrontElementBase):
    pass


class NamedContainerBase(FrontContainerBase):
    def __init__(self, children: Iterable[FrontElementBase] = None, name: str = None):
        super().__init__(children)
        self.name = name


class DagContainerBase(NamedContainerBase):
    def __init__(
        self, dag: DAG, children: Iterable[FrontElementBase] = None, name: str = None
    ):
        super().__init__(children, name)
        self.dag = dag


class InputBase(FrontComponentBase):
    def __init__(self, label: str, input_key: str = None, init_value: Any = None):
        super().__init__()
        self.label = label
        self.input_key = input_key
        self.init_value = init_value


class TextInputBase(InputBase):
    def __init__(
        self, label: str, input_key: str = None, init_value: Any = None
    ) -> None:
        super().__init__(label, input_key, init_value)
        self.init_value = str(self.init_value) if self.init_value is not None else ''


class NumberInputBase(InputBase):
    def __init__(
        self,
        label: str,
        input_key: str = None,
        init_value: Any = None,
        min_value=None,
        max_value=None,
        format: str = None,
    ):
        super().__init__(label, input_key, init_value)
        self.min_value = min_value
        self.max_value = max_value
        self.format = format


class IntInputBase(NumberInputBase):
    def __init__(
        self,
        label: str,
        input_key: str = None,
        init_value: Any = None,
        min_value: int = None,
        max_value: int = None,
        format: str = None,
    ):
        super().__init__(label, input_key, init_value, min_value, max_value, format)
        self.init_value = int(self.init_value) if self.init_value is not None else 0


class FloatInputBase(NumberInputBase):
    def __init__(
        self,
        label: str,
        input_key: str = None,
        init_value: Any = None,
        min_value: float = None,
        max_value: float = None,
        format: str = None,
        step: float = None,
    ):
        super().__init__(label, input_key, init_value, min_value, max_value, format)
        self.init_value = float(self.init_value) if self.init_value is not None else 0.0
        self.step = step


class GraphBase(FrontComponentBase):
    def __init__(self, figure_or_dot: Any, use_container_width: bool = False):
        super().__init__()
        self.figure_or_dot = figure_or_dot
        self.use_container_width = use_container_width
