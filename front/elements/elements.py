from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable, List, Optional, TypedDict, Union
from i2 import Sig
from inspect import _empty
from front.types import FrontElementName
from front.util import deep_merge

# ================================== ELEMENT IDS ==================================
# CONTAINERS
APP_CONTAINER = '72aa8125-597f-4f4b-8820-88ac037670ab'
VIEW_CONTAINER = '7fee36ae-6921-4f30-9231-64288e930964'
SECTION_CONTAINER = '8a1750ab-6608-4cab-a2e4-377d1ea5991a'
EXEC_SECTION_CONTAINER = '9e3d7a51-00e0-4973-b3cf-db6b7d9a6ba8'
MULTI_SOURCE_INPUT_CONTAINER = 'def87219-642d-40b1-ba16-b29b0519bda4'

# COMPONENTS
TEXT_INPUT_COMPONENT = '8e58f1c6-639f-47b7-9c28-184d559366de'
TEXT_INPUT_COMPONENT_AREA = 'bcdcbcd5-2aee-428b-a7fc-0ad35f58f9fe'
TEXT_OUTPUT_COMPONENT = '31d8cf81-7490-4cc5-8e6d-f71093776f33'

INT_INPUT_COMPONENT = '542847a3-2458-4ca1-a36b-be0c4a918e73'
INT_INPUT_SLIDER_COMPONENT = '4b906006-7c9d-40a2-9856-0f827e98a231'

FLOAT_INPUT_COMPONENT = '918ece4f-2fe4-47a8-a0dc-28a75b0986c4'
FLOAT_INPUT_SLIDER_COMPONENT = 'ac5c1a38-7a17-4f9f-be10-395774bc16e8'

FILE_UPLOADER_COMPONENT = '4d3ad1f6-b5d7-4404-b383-522f58ccf93a'
AUDIO_RECORDER_COMPONENT = '3cdcc586-bf4b-412b-a5a1-9fd5e47f25c9'
# =================================================================================


class FrontElementBase(ABC):
    def __init__(self, obj=None, name: FrontElementName = None):
        self.obj = obj
        name = name(obj) if isinstance(name, Callable) else name
        self.name = name or ''

    @abstractmethod
    def render(self):
        # raise NotImplementedError('This method needs to be implemented in subclasses.')
        pass


ELEMENT_KEY = '_front_element'
STORED_VALUE_GETTER = 'stored_value_getter'

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


def mk_input_element_specs(obj, inputs):
    def mk_input_spec(p):
        annot = p.annotation if p.annotation != _empty else None
        param_type = annot or (type(p.default) if p.default != _empty else Any)
        input_spec = inputs_spec.get(p.name)
        if not input_spec:
            input_spec = inputs_spec.get(param_type)
        if not input_spec:
            input_spec = inputs_spec[Any]
        dflt_input_key = f'{obj.__name__}_{p.name}'
        input_key = input_spec.get('input_key', dflt_input_key)
        stored_value = stored_value_getter(input_key)
        init_value = (
            stored_value
            if stored_value is not None
            else (p.default if p.default != _empty else None)
        )
        return dict(input_spec, obj=p, input_key=input_key, init_value=init_value)

    inputs_spec = dict(inputs)
    default = inputs_spec.pop('_default', {})
    inputs_spec = {k: deep_merge(default, v) for k, v in inputs_spec.items()}
    sig = Sig(obj)
    stored_value_getter = getattr(obj, STORED_VALUE_GETTER, lambda x: None)
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


class FrontComponentBase(FrontElementBase):
    pass


class ExecContainerBase(FrontContainerBase):
    def __init__(self, obj: Callable, inputs: dict, name: FrontElementName = None):
        element_specs = mk_input_element_specs(obj, inputs)
        super().__init__(obj=obj, name=name, **element_specs)


class InputBase(FrontComponentBase):
    def __init__(
        self,
        obj=None,
        name: FrontElementName = None,
        input_key: str = None,
        init_value: Any = None,
    ):
        super().__init__(obj=obj, name=name)
        self.input_key = input_key
        self.init_value = init_value


class MultiSourceInputContainerBase(FrontContainerBase):
    def __init__(
        self,
        obj=None,
        name: FrontElementName = None,
        input_key: str = None,
        init_value: Any = None,
        **kwargs: FrontElementSpec,
    ):
        # TODO: This is definitely not the right way spread the input_key and
        # init_value to the child input components since a value can be compatible
        # with some compoenents and incompatible with others.
        # Just ignoring them for now.
        # kwargs = {
        #     k: dict(v, input_key=input_key, init_value=init_value)
        #     for k, v in kwargs.items()
        # }
        super().__init__(obj=obj, name=name, **kwargs)


class TextInputBase(InputBase):
    def __init__(
        self,
        obj=None,
        name: FrontElementName = None,
        input_key: str = None,
        init_value: Any = None,
    ):
        super().__init__(obj=obj, name=name, input_key=input_key, init_value=init_value)
        self.init_value = str(self.init_value) if self.init_value is not None else ''


class NumberInputBase(InputBase):
    def __init__(
        self,
        obj=None,
        name: FrontElementName = None,
        input_key: str = None,
        init_value: Any = None,
        min_value=None,
        max_value=None,
        format: str = None,
    ):
        super().__init__(obj=obj, name=name, input_key=input_key, init_value=init_value)
        self.min_value = min_value
        self.max_value = max_value
        self.format = format


class IntInputBase(NumberInputBase):
    def __init__(
        self,
        obj=None,
        name: FrontElementName = None,
        input_key: str = None,
        init_value: Any = None,
        min_value: int = None,
        max_value: int = None,
        format: str = None,
    ):
        super().__init__(
            obj=obj,
            name=name,
            input_key=input_key,
            init_value=init_value,
            min_value=min_value,
            max_value=max_value,
            format=format,
        )
        self.init_value = int(self.init_value) if self.init_value is not None else 0


class FloatInputBase(NumberInputBase):
    def __init__(
        self,
        obj=None,
        name: FrontElementName = None,
        input_key: str = None,
        init_value: Any = None,
        min_value: float = None,
        max_value: float = None,
        format: str = None,
        step: float = None,
    ):
        super().__init__(
            obj=obj,
            name=name,
            input_key=input_key,
            init_value=init_value,
            min_value=min_value,
            max_value=max_value,
            format=format,
        )
        self.init_value = float(self.init_value) if self.init_value is not None else 0.0
        self.step = step


class FileUploaderBase(InputBase):
    def __init__(
        self,
        obj=None,
        name: FrontElementName = None,
        input_key: str = None,
        init_value: Any = None,
        type: Optional[Union[str, List[str]]] = None,
    ) -> None:
        super().__init__(obj=obj, name=name, input_key=input_key, init_value=init_value)
        self.type = type
