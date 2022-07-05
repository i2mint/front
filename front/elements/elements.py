from abc import ABC, abstractmethod
from typing import Any, Iterable, List, Optional, Union
from meshed import DAG


class FrontElementBase(ABC):
    def __init__(self, name: str = None):
        self.name = name

    @abstractmethod
    def render(self):
        # raise NotImplementedError('This method needs to be implemented in subclasses.')
        pass


class FrontContainerBase(FrontElementBase):
    children: Iterable[FrontElementBase]

    def __init__(self, name: str = None, children: Iterable[FrontElementBase] = None):
        super().__init__(name)
        self.children = children or []

    def _render_children(self):
        for child in self.children:
            child.render()


class FrontComponentBase(FrontElementBase):
    pass


class DagContainerBase(FrontContainerBase):
    def __init__(
        self, dag: DAG, name: str = None, children: Iterable[FrontElementBase] = None
    ):
        super().__init__(name, children)
        self.dag = dag


class InputBase(FrontComponentBase):
    def __init__(self, name: str, input_key: str = None, init_value: Any = None):
        super().__init__(name)
        self.input_key = input_key
        self.init_value = init_value


class MultiSourceInputContainerBase(FrontContainerBase):
    def __init__(self, name: str, children: Iterable[InputBase] = None):
        super().__init__(name, children)


class TextInputBase(InputBase):
    def __init__(
        self, name: str, input_key: str = None, init_value: Any = None
    ) -> None:
        super().__init__(name, input_key, init_value)
        self.init_value = str(self.init_value) if self.init_value is not None else ''


class NumberInputBase(InputBase):
    def __init__(
        self,
        name: str,
        input_key: str = None,
        init_value: Any = None,
        min_value=None,
        max_value=None,
        format: str = None,
    ):
        super().__init__(name, input_key, init_value)
        self.min_value = min_value
        self.max_value = max_value
        self.format = format


class IntInputBase(NumberInputBase):
    def __init__(
        self,
        name: str,
        input_key: str = None,
        init_value: Any = None,
        min_value: int = None,
        max_value: int = None,
        format: str = None,
    ):
        super().__init__(name, input_key, init_value, min_value, max_value, format)
        self.init_value = int(self.init_value) if self.init_value is not None else 0


class FloatInputBase(NumberInputBase):
    def __init__(
        self,
        name: str,
        input_key: str = None,
        init_value: Any = None,
        min_value: float = None,
        max_value: float = None,
        format: str = None,
        step: float = None,
    ):
        super().__init__(name, input_key, init_value, min_value, max_value, format)
        self.init_value = float(self.init_value) if self.init_value is not None else 0.0
        self.step = step


class FileUploaderBase(InputBase):
    def __init__(
        self,
        name: str,
        input_key: str = None,
        init_value: Any = None,
        type: Optional[Union[str, List[str]]] = None,
    ) -> None:
        super().__init__(name, input_key, init_value)
        self.type = type


class GraphBase(FrontComponentBase):
    def __init__(self, figure_or_dot: Any, use_container_width: bool = False):
        super().__init__()
        self.figure_or_dot = figure_or_dot
        self.use_container_width = use_container_width
