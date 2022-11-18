from abc import ABC, abstractmethod
from dataclasses import dataclass
from threading import Timer
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Literal,
    Optional,
    TypedDict,
    Union,
    get_args,
    get_origin,
)
from front.data_binding import BoundData, ValueNotSet
from i2 import Sig
from inspect import _empty
from front.types import FrontElementName
from front.util import deep_merge, get_value
from i2.signatures import call_forgivingly
from pydantic import validate_arguments
from front.data_binding import Binder as b


@dataclass
class FrontElementBase(ABC):
    obj: Any = None
    name: FrontElementName = None

    def __post_init__(self):
        self.name = get_value(self.name, self.obj) or ''

    def pre_render(self):
        pass

    @abstractmethod
    def render(self):
        pass

    def post_render(self, render_result):
        return render_result

    def __call__(self):
        self.pre_render()
        r = self.render()
        return self.post_render(r)


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
    try:
        return factory(**_spec)
    except Exception as e:
        print(f'An error occurred when trying to build element {factory}')
        raise e


def mk_input_element_specs(obj, inputs):
    def mk_input_spec(p):
        input_spec = inputs_spec.get(p.name, {})
        annot = p.annotation if p.annotation != _empty else None
        param_type = annot or (type(p.default) if p.default != _empty else Any)
        param_origin_type = get_origin(param_type)
        is_noneable = p.default is None
        if param_origin_type == Union:
            types = list(get_args(param_type))
            none_type = type(None)
            if none_type in types:
                types.remove(none_type)
                is_noneable = True
            if len(types) > 1:
                raise NotImplementedError('Union type is not supported yet.')
            param_type = types[0]
        else:
            param_type = param_origin_type or param_type
        if param_type not in inputs_spec:
            param_type = Any
        type_spec = inputs_spec.get(param_type, {})
        input_spec = deep_merge(type_spec, input_spec)
        value = input_spec.get('value')
        input_key = value.id if value else f'{obj.__name__}_{p.name}'
        return dict(input_spec, obj=p, input_key=input_key, is_noneable=is_noneable)

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
        self.children = list(map(mk_element_from_spec, specs))

    def _render_children(self):
        for child in self.children:
            child()


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
    value: Any = ValueNotSet
    on_value_change: Callable[..., None] = None
    bound_data_factory: Callable = None
    is_noneable: bool = False
    disabled: bool = False

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.value, BoundData):
            value = self.value
            self.value = self._create_bound_data(self.value_key)
            if self.value.get() is ValueNotSet and value is not ValueNotSet:
                self.value.set(value)
        dflt_value = self.obj.default
        if self.value.get() is ValueNotSet and dflt_value != _empty:
            self.value.set(dflt_value)
        self._init_view_value()
        self._init_none_value()

    def on_change(self):
        value = self.value.get()
        if self.on_value_change and value is not ValueNotSet:
            call_forgivingly(self.on_value_change, self.value.get())

    # def pre_render(self):
    #     super().pre_render()
    #     if self.value.id != self.input_key:
    #         new_value = getattr(b, self.input_key).get()
    #         if new_value is not ValueNotSet and new_value != self.value.get():
    #             self.value.set(new_value)
    #             self._call_on_value_change()

    def post_render(self, render_result):
        self.value.set(render_result)
        return render_result

    @property
    def value_key(self) -> str:
        return self._build_key('value')

    @property
    def view_key(self) -> str:
        return self._build_key('view')

    @property
    def none_key(self) -> str:
        return self._build_key('none')

    def _build_key(self, suffix: str):
        return f'{self.input_key}_{suffix}'

    @property
    def _dflt_view_value(self) -> Any:
        return None

    def _get_view_value(self):
        return self.value.get() or self._dflt_view_value

    def _init_view_value(self):
        self.view_value = self._create_bound_data(self.view_key)
        if self.view_value.get() is ValueNotSet:
            self.view_value.set(self._get_view_value())

    def _init_none_value(self):
        self.none_value = self._create_bound_data(self.none_key)
        if self.none_value.get() is ValueNotSet:
            self.none_value.set(self.value.get() is None)

    def _create_bound_data(self, key):
        if self.bound_data_factory is None:
            raise ValueError(
                f'No factory provided to build a BoundData instance with id \
                    {key}'
            )
        return self.bound_data_factory(key)


class OutputBase(FrontComponentBase):
    output: Any = None


class ExecContainerBase(FrontContainerBase):
    def __init__(
        self,
        obj: Callable,
        inputs: dict,
        output: dict,
        name: FrontElementName = None,
        auto_submit: bool = False,
        on_submit: Callable[[Any], None] = None,
    ):
        self.inputs = inputs
        self._feed_kwargs_input_spec()
        element_specs = dict(mk_input_element_specs(obj, inputs), output=output)
        super().__init__(obj=obj, name=name, **element_specs)
        self.auto_submit = auto_submit
        self.on_submit = on_submit

    def _feed_kwargs_input_spec(self):
        inputs_spec = dict(self.inputs)
        kwargs_spec = inputs_spec.pop('kwargs', None)
        if kwargs_spec:
            self.inputs['kwargs']['inputs'] = inputs_spec

    def _render_inputs(self):
        input_components = [
            self._noneable(child) if child.is_noneable else child
            for child in self.children
            if isinstance(child, InputBase)
        ]
        return {
            input_component.obj.name: input_component()
            for input_component in input_components
        }

    @abstractmethod
    def _noneable(self, input: InputBase) -> InputBase:
        pass

    def _submit(self, inputs):
        # There is a pending bug in pydantic that transforms types to <type>_iterator
        # and make the app failing: https://github.com/pydantic/pydantic/issues/3581
        # pydantic_obj = validate_arguments(self.obj)
        # output = pydantic_obj(**inputs)
        output = self.obj(**inputs)
        output_component = next(
            iter(child for child in self.children if isinstance(child, OutputBase))
        )
        output_component.output = output
        output_component()
        if self.on_submit:
            self.on_submit(output)


class MultiSourceInputBase(InputBase):
    def __init__(
        self,
        obj=None,
        name: FrontElementName = None,
        input_key: str = None,
        value: Any = ValueNotSet,
        on_value_change: Callable[..., None] = None,
        bound_data_factory: Callable = None,
        is_noneable: bool = False,
        disabled: bool = False,
        **kwargs: FrontElementSpec,
    ):
        super().__init__(
            obj=obj,
            name=name,
            input_key=input_key,
            value=value,
            on_value_change=on_value_change,
            bound_data_factory=bound_data_factory,
            is_noneable=is_noneable,
            disabled=disabled,
        )
        specs = [
            dict(
                obj=self.obj,
                name=k,
                value=self.value,
                on_value_change=self.on_value_change,
                **v,
            )
            for k, v in kwargs.items()
        ]
        self.input_components = list(map(mk_element_from_spec, specs))

        # TODO: This is definitely not the right way to spread the input_key and
        # init_value to the child input components since a value can be compatible
        # with some compoenents and incompatible with others.
        # Just ignoring them for now.
        # kwargs = {
        #     k: dict(v, input_key=input_key, init_value=init_value)
        #     for k, v in kwargs.items()
        # }
        # super().__init__(
        #     obj=obj,
        #     name=name,
        #     **kwargs
        # )


@dataclass
class TextInputBase(InputBase):
    @property
    def _dflt_view_value(self):
        return ''


@dataclass
class BooleanInputBase(InputBase):
    @property
    def _dflt_view_value(self):
        return False


@dataclass
class NumberInputBase(InputBase):
    format: str = None


@dataclass
class IntInputBase(NumberInputBase):
    min_value: int = None
    max_value: int = None

    @property
    def _dflt_view_value(self):
        return 0


@dataclass
class FloatInputBase(NumberInputBase):
    min_value: float = None
    max_value: float = None
    step: float = None

    @property
    def _dflt_view_value(self):
        return 0.0


@dataclass
class FileUploaderBase(InputBase):
    type: Optional[Union[str, List[str]]] = None


SELECT_BOX_DFLT_INDEX = 0


@dataclass
class SelectBoxBase(InputBase):
    options: Union[Iterable, BoundData] = None

    def __post_init__(self):
        super().__post_init__()
        self.options = self.options or []

    def pre_render(self):
        super().pre_render()
        options = self._ensure_options()
        if not options:
            annot = self.obj.annotation
            if get_origin(annot) == Literal:
                options = list(get_args(annot))
        self._options = list(options)
        if self._options:
            view_value = self.view_value.get()
            self._preselected_index = (
                self._options.index(view_value)
                if view_value in self._options
                else SELECT_BOX_DFLT_INDEX
            )
            selected_value = self._options[self._preselected_index]
            if selected_value != view_value:
                self.view_value.set(selected_value)

    @property
    def _dflt_view_value(self) -> Any:
        options = self._ensure_options()
        return options[SELECT_BOX_DFLT_INDEX] if options else None

    def _ensure_options(self):
        return self.options() if callable(self.options) else self.options


@dataclass
class KwargsInputBase(InputBase):
    inputs: dict = None
    func_sig: Sig = None

    def __post_init__(self):
        super().__post_init__()

        @self.func_sig
        def get_kwargs(**kwargs):
            return kwargs

        self.get_kwargs = get_kwargs

    def _get_kwargs(self, **kwargs):
        return kwargs

    def _return_kwargs(self, output):
        self.value.set(output)
