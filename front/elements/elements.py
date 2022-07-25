from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Optional, TypedDict, Union
from i2 import Sig
from inspect import _empty
from front.types import FrontElementName
from front.util import deep_merge, get_value


@dataclass
class FrontElementBase(ABC):
    obj: Any = None
    name: FrontElementName = None

    def __post_init__(self):
        self.name = get_value(self.name, self.obj) or ''

    @abstractmethod
    def render(self):
        # raise NotImplementedError('This method needs to be implemented in subclasses.')
        pass


ELEMENT_KEY = '_front_element'
DEFAULT_INPUT_KEY = '_default'
FrontElementSpec = TypedDict('FrontElementSpec', {ELEMENT_KEY: FrontElementBase})


def mk_element_from_spec(spec: FrontElementSpec):
    _spec = dict(spec)
    try:
        factory = _spec.pop(ELEMENT_KEY)
    except KeyError:
        raise RuntimeError(
            f'Key "{ELEMENT_KEY}" is missing in the following element specification: \
                {spec}'
        )
    return factory(**_spec)


def mk_input_element_specs(obj, inputs, stored_value_getter):
    def mk_input_spec(p):
        input_spec = inputs_spec.get(p.name, {})
        annot = p.annotation if p.annotation != _empty else None
        param_type = annot or (type(p.default) if p.default != _empty else Any)
        if param_type not in inputs_spec:
            param_type = Any
        type_spec = inputs_spec.get(param_type, {})
        input_spec = deep_merge(type_spec, input_spec)
        dflt_input_key = f'{obj.__name__}_{p.name}'
        input_key = input_spec.get('input_key', dflt_input_key)
        stored_value = stored_value_getter(input_key) if stored_value_getter else None
        init_value = (
            stored_value
            if stored_value is not None
            else (p.default if p.default != _empty else None)
        )
        return dict(input_spec, obj=p, input_key=input_key, init_value=init_value)

    inputs_spec = dict(inputs)
    default = inputs_spec.pop(DEFAULT_INPUT_KEY, {})
    inputs_spec = {k: deep_merge(default, v) for k, v in inputs_spec.items()}
    sig = Sig(obj)
    elements_spec = {p.name: mk_input_spec(p) for p in sig.params}
    return elements_spec


class FrontContainerBase(FrontElementBase):
    children: Iterable[FrontElementBase]

    def __init__(
        self, obj=None, name: FrontElementName = None, **kwargs: FrontElementSpec
    ):
        super().__init__(obj=obj, name=name)
        specs = [dict(dict(name=k, obj=obj), **v) for k, v in kwargs.items()]
        self._mk_children(specs)

    def _mk_children(self, specs):
        self.children = list(map(mk_element_from_spec, specs))

    def _render_children(self):
        for child in self.children:
            child.render()


@dataclass
class FrontComponentBase(FrontElementBase):
    pass


class TextSectionBase(FrontComponentBase):
    def __init__(
        self,
        content: str,
        kind: str = 'text',
        obj: Any = None,
        name: FrontElementName = None,
        **kwargs,
    ):
        super().__init__(obj, name)
        self.content = get_value(content, self.obj) or ''
        self.kind = get_value(kind, self.obj)
        self.kwargs = kwargs


@dataclass
class InputBase(FrontComponentBase):
    input_key: str = None
    init_value: Any = None


class OutputBase(FrontComponentBase):
    output: Any = None

    def render_output(self, output):
        self.output = output
        return self.render()


class ExecContainerBase(FrontContainerBase):
    def __init__(
        self,
        obj: Callable,
        inputs: dict,
        output: dict,
        name: FrontElementName = None,
        stored_value_getter: Callable[[str], Any] = None,
    ):
        element_specs = dict(
            mk_input_element_specs(obj, inputs, stored_value_getter), output=output
        )
        super().__init__(obj=obj, name=name, **element_specs)

    @property
    def input_components(self) -> Iterable[InputBase]:
        return [
            child
            for child in self.children
            if isinstance(child, InputBase)
            or isinstance(child, MultiSourceInputContainerBase)
        ]

    @property
    def output_component(self) -> OutputBase:
        return next(
            iter(child for child in self.children if isinstance(child, OutputBase))
        )


class MultiSourceInputContainerBase(FrontContainerBase):
    def __init__(
        self,
        obj=None,
        name: FrontElementName = None,
        input_key: str = None,
        init_value: Any = None,
        **kwargs: FrontElementSpec,
    ):
        # TODO: This is definitely not the right way to spread the input_key and
        # init_value to the child input components since a value can be compatible
        # with some compoenents and incompatible with others.
        # Just ignoring them for now.
        # kwargs = {
        #     k: dict(v, input_key=input_key, init_value=init_value)
        #     for k, v in kwargs.items()
        # }
        super().__init__(obj=obj, name=name, **kwargs)


@dataclass
class TextInputBase(InputBase):
    def __post_init__(self):
        super().__post_init__()
        self.init_value = str(self.init_value) if self.init_value is not None else ''


@dataclass
class NumberInputBase(InputBase):
    format: str = None


@dataclass
class IntInputBase(NumberInputBase):
    min_value: int = None
    max_value: int = None

    def __post_init__(self):
        super().__post_init__()
        self.init_value = int(self.init_value) if self.init_value is not None else 0


@dataclass
class FloatInputBase(NumberInputBase):
    min_value: float = None
    max_value: float = None
    step: float = None

    def __post_init__(self):
        super().__post_init__()
        self.init_value = float(self.init_value) if self.init_value is not None else 0.0


@dataclass
class FileUploaderBase(InputBase):
    type: Optional[Union[str, List[str]]] = None


@dataclass
class SelectBoxBase(InputBase):
    options: Iterable = None

    def __post_init__(self):
        super().__post_init__()
        self.options = self.options or []
