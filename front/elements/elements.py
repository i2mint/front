"""Abstract base classes for the composite tree of front UI elements.

Front elements (containers, inputs, outputs, etc.) are arranged in a tree
mirroring the rendering specification. This module defines the base
``FrontElementBase`` and ``FrontContainerBase`` classes that concrete frontends
(e.g. streamlit) subclass to provide their own rendering.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from threading import Timer
from typing import (
    Any,
    List,
    Literal,
    Optional,
    TypedDict,
    Union,
    get_args,
    get_origin,
)
from collections.abc import Callable, Iterable, Sequence
from front.data_binding import BoundData, ValueNotSet
from i2 import Sig
from inspect import _empty
from front.types import FrontElementDisplay, FrontElementName
from front.util import deep_merge, get_value, param_default
from i2.signatures import call_forgivingly

# from pydantic import validate_arguments
from front.data_binding import Binder as b


@dataclass
class FrontElementBase(ABC):
    """Base of every front element: a renderable node of the element tree.

    Subclasses implement ``render``. Calling the element runs the lifecycle
    ``pre_render`` → ``render`` → ``post_render`` when ``display`` is truthy, and
    does nothing (returns None) otherwise. ``name`` and ``display`` may be given
    as callables of ``obj``; they are resolved at construction.

    >>> from dataclasses import dataclass
    >>> @dataclass
    ... class Hello(FrontElementBase):
    ...     def render(self):
    ...         return f"hello {self.name}"
    >>> Hello(name='world')()
    'hello world'
    >>> Hello(obj=len, name=lambda obj: obj.__name__)()
    'hello len'
    >>> Hello(name='hidden', display=False)() is None
    True

    See Also:
        ``FrontContainerBase``: an element with children.
        ``FrontComponentBase``: a leaf element the user interacts with.
    """

    obj: Any = None
    name: FrontElementName = None
    display: FrontElementDisplay = True

    def __post_init__(self):
        self.name = get_value(self.name, self.obj) or ""
        self.display = get_value(self.display, self.obj)

    def pre_render(self):
        """Hook run before ``render``; does nothing by default."""
        pass

    @abstractmethod
    def render(self):
        """Render the element with the concrete UI framework; must be overridden."""
        pass

    def post_render(self, render_result):
        """Hook run on the result of ``render``; returns it unchanged by default."""
        return render_result

    def __call__(self):
        """Run ``pre_render`` → ``render`` → ``post_render`` if ``display``, else return None."""
        if self.display:
            self.pre_render()
            r = self.render()
            return self.post_render(r)


ELEMENT_KEY = "_front_element"
DEFAULT_INPUT_KEY = "_default"
FrontElementSpec = TypedDict("FrontElementSpec", {ELEMENT_KEY: FrontElementBase})


def mk_element_from_spec(spec: FrontElementSpec):
    """Instantiate the element factory found under ``ELEMENT_KEY`` with the other keys.

    >>> from dataclasses import dataclass
    >>> @dataclass
    ... class Hello(FrontElementBase):
    ...     def render(self):
    ...         return f"hello {self.name}"
    >>> mk_element_from_spec({ELEMENT_KEY: Hello, 'name': 'x'})()
    'hello x'

    :raises RuntimeError: If ``spec`` has no ``ELEMENT_KEY``.
    """
    _spec = dict(spec)
    try:
        factory = _spec.pop(ELEMENT_KEY)
    except KeyError:
        raise RuntimeError(
            f'Key "{ELEMENT_KEY}" is missing in the following element specification: {spec}'
        )
    try:
        return factory(**_spec)
    except Exception as e:
        print(f"An error occurred when trying to build element {factory}")
        raise e


def mk_input_element_specs(obj, inputs):
    """Make one input element spec per parameter of ``obj``, from a type-keyed ``inputs`` spec.

    ``inputs`` maps parameter types (and/or parameter names) to element specs; the
    ``DEFAULT_INPUT_KEY`` entry is merged under every type entry. Each parameter's
    spec is looked up by its annotation (or the type of its default), with an
    ``Optional[X]`` annotation or a ``None`` default marking it as ``is_noneable``.
    Unions of more than one non-None type are not supported.

    >>> def foo(a: int, b='hi', c: float = None):
    ...     pass
    >>> specs = mk_input_element_specs(
    ...     foo, {DEFAULT_INPUT_KEY: {'disabled': False}, int: {'min_value': 0}}
    ... )
    >>> list(specs)
    ['a', 'b', 'c']
    >>> {k: v for k, v in specs['a'].items() if k != 'obj'}
    {'disabled': False, 'min_value': 0, 'input_key': 'foo_a', 'is_noneable': False}
    >>> specs['c']['is_noneable']
    True

    :raises NotImplementedError: If a parameter is annotated with a Union of several
        non-None types.
    """

    def mk_input_spec(p):
        input_spec = inputs_spec.get(p.name, {})
        annot = p.annotation if p.annotation != _empty else None
        default = param_default(p)
        param_type = annot or (type(default) if default != _empty else Any)
        param_origin_type = get_origin(param_type)
        is_noneable = default is None
        if param_origin_type == Union:
            types = list(get_args(param_type))
            none_type = type(None)
            if none_type in types:
                types.remove(none_type)
                is_noneable = True
            if len(types) > 1:
                raise NotImplementedError("Union type is not supported yet.")
            param_type = types[0]
        else:
            param_type = param_origin_type or param_type
        if param_type not in inputs_spec:
            param_type = Any
        type_spec = inputs_spec.get(param_type, {})
        input_spec = deep_merge(type_spec, input_spec)
        value = input_spec.get("value")
        input_key = (
            value.id if isinstance(value, BoundData) else f"{obj.__name__}_{p.name}"
        )
        return dict(input_spec, obj=p, input_key=input_key, is_noneable=is_noneable)

    inputs_spec = dict(inputs)
    default = inputs_spec.pop(DEFAULT_INPUT_KEY, {})
    inputs_spec = {k: deep_merge(default, v) for k, v in inputs_spec.items()}
    sig = Sig(obj)
    elements_spec = {p.name: mk_input_spec(p) for p in sig.params}
    return elements_spec


class FrontContainerBase(FrontElementBase):
    """An element with children, each built from a keyword argument holding an element spec.

    Every extra keyword argument is a child spec: the key becomes the child's
    ``name`` (unless the spec overrides it) and the container's ``obj`` is passed
    down. Concrete containers define the layout in ``render``.

    >>> from dataclasses import dataclass
    >>> @dataclass
    ... class Hello(FrontElementBase):
    ...     def render(self):
    ...         return f"hello {self.name}"
    >>> class Box(FrontContainerBase):
    ...     def render(self):
    ...         return [child() for child in self.children]
    >>> box = Box(name='box', greeting={ELEMENT_KEY: Hello, 'name': 'you'}, other={ELEMENT_KEY: Hello})
    >>> box()
    ['hello you', 'hello other']
    """

    children: Iterable[FrontElementBase]

    def __init__(
        self,
        obj=None,
        name: FrontElementName = None,
        display: FrontElementDisplay = True,
        **kwargs: FrontElementSpec,
    ):
        super().__init__(obj=obj, name=name, display=display)
        specs = [dict(dict(name=k, obj=obj), **v) for k, v in kwargs.items()]
        self.children = [mk_element_from_spec(spec) for spec in specs]

    def _render_children(self):
        for child in self.children:
            child()


@dataclass
class FrontComponentBase(FrontElementBase):
    """A leaf element the user interacts with (an input, an output, a text section)."""

    pass


class TextSectionBase(FrontComponentBase):
    """A component displaying text ``content`` of a given ``kind`` (e.g. "text", "markdown").

    ``content`` and ``kind`` may be callables of ``obj``, resolved at construction.
    Extra keyword arguments are kept in ``self.kwargs`` for the concrete renderer.
    """

    def __init__(
        self,
        content: str,
        kind: str = "text",
        obj: Any = None,
        name: FrontElementName = None,
        display: FrontElementDisplay = True,
        **kwargs,
    ):
        super().__init__(obj=obj, name=name, display=display)
        self.content = get_value(content, self.obj) or ""
        self.kind = get_value(kind, self.obj)
        self.kwargs = kwargs


@dataclass
class InputBase(FrontComponentBase):
    """Base of input components: a value bound to state under ``input_key``.

    ``obj`` is the ``inspect.Parameter`` the input feeds. At construction, ``value``
    is wrapped in a ``BoundData`` made by ``bound_data_factory`` (unless it already
    is one), and seeded with the given value or the parameter's default if nothing
    is set yet. Two companion keys, ``view_key`` and ``none_key``, hold the widget's
    displayed value and its "is None" toggle.

    :raises ValueError: If ``bound_data_factory`` is None when a ``BoundData`` is needed.
    """

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
            self.value = self._create_bound_data(self.input_key)
            if self.value.get() is ValueNotSet and value is not ValueNotSet:
                self.value.set(value)
        dflt_value = param_default(self.obj)
        if self.value.get() is ValueNotSet and dflt_value != _empty:
            self.value.set(dflt_value)
        self._init_view_value()
        self._init_none_value()

    def on_change(self):
        """Call ``on_value_change`` with the current view value, if both are set."""
        if (
            self.on_value_change
            and (view_value := self._create_bound_data(self.view_key).get())
            is not ValueNotSet
        ):
            call_forgivingly(self.on_value_change, view_value)

    def post_render(self, render_result):
        """Store the rendered (widget) value in the bound state and return it."""
        self.value.set(render_result)
        return render_result

    @property
    def view_key(self) -> str:
        """State key of the widget's displayed value: ``"{input_key}_view"``."""
        return self._build_key("view")

    @property
    def none_key(self) -> str:
        """State key of the "value is None" toggle: ``"{input_key}_none"``."""
        return self._build_key("none")

    def _build_key(self, suffix: str):
        return f"{self.input_key}_{suffix}"

    @property
    def _type(self):
        return str

    @property
    def _dflt_view_value(self):
        return None

    def _get_init_view_value(self):
        value = self.value.get()
        if value in [None, ValueNotSet]:
            return self._dflt_view_value
        return self._type(value)

    def _init_view_value(self):
        view_value = self._create_bound_data(self.view_key).get()
        self.view_value = (
            view_value if view_value is not ValueNotSet else self._get_init_view_value()
        )

    def _init_none_value(self):
        none_value = self._create_bound_data(self.none_key).get()
        self.none_value = (
            none_value if none_value is not ValueNotSet else self.value.get() is None
        )

    def _create_bound_data(self, key):
        if self.bound_data_factory is None:
            raise ValueError(
                f'No factory provided to build a BoundData instance with id "{key}"'
            )
        return self.bound_data_factory(key)


class OutputBase(FrontComponentBase):
    """Base of output components; ``output`` is set by the executing container before render."""

    output: Any = None


class ExecContainerBase(FrontContainerBase):
    """Container that executes ``obj`` with the values of its input children.

    Builds one input child per parameter of ``obj`` (see ``mk_input_element_specs``)
    plus an ``output`` child. ``_submit`` calls ``obj`` with the collected inputs,
    hands the result to the first ``OutputBase`` child and renders it, then calls
    ``on_submit`` with the result if given. Concrete subclasses implement ``render``
    and ``_noneable`` (how an optional input is presented).
    """

    def __init__(
        self,
        obj: Callable,
        inputs: dict,
        output: dict,
        name: FrontElementName = None,
        display: FrontElementDisplay = True,
        auto_submit: bool = False,
        on_submit: Callable[[Any], None] = None,
    ):
        self.inputs = inputs
        self._feed_kwargs_input_spec()
        element_specs = dict(mk_input_element_specs(obj, inputs), output=output)
        super().__init__(obj=obj, name=name, display=display, **element_specs)
        self.auto_submit = auto_submit
        self.on_submit = on_submit

    def _feed_kwargs_input_spec(self):
        inputs_spec = dict(self.inputs)
        kwargs_spec = inputs_spec.pop("kwargs", None)
        if kwargs_spec:
            kwargs_inputs = kwargs_spec.get("inputs", {})
            kwargs_inputs = deep_merge(inputs_spec, kwargs_inputs)
            self.inputs["kwargs"]["inputs"] = kwargs_inputs

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
        sig = Sig(self.obj)
        args, kwargs = sig.extract_args_and_kwargs(**inputs)
        if sig.var_keyword_name:
            var_keyword = kwargs.pop(sig.var_keyword_name, {})
            kwargs = dict(kwargs, **var_keyword)
        output = self.obj(*args, **kwargs)
        output_component = next(
            iter(child for child in self.children if isinstance(child, OutputBase))
        )
        output_component.output = output
        output_component()
        if self.on_submit:
            self.on_submit(output)


class MultiSourceInputBase(InputBase):
    """An input whose value can come from several child input components.

    Extra keyword arguments are child input specs; each child shares this input's
    ``input_key``, ``value`` and binding settings.
    """

    def __init__(
        self,
        obj=None,
        name: FrontElementName = None,
        display: FrontElementDisplay = True,
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
            display=display,
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
                input_key=self.input_key,
                value=self.value,
                on_value_change=self.on_value_change,
                bound_data_factory=self.bound_data_factory,
                is_noneable=self.is_noneable,
                disabled=self.disabled,
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
    """Text input; the view value defaults to the empty string."""

    type: str = None

    @property
    def _dflt_view_value(self):
        return ""


@dataclass
class BooleanInputBase(InputBase):
    """Boolean input (checkbox-like); values are cast with ``bool``, defaulting to False."""

    @property
    def _type(self):
        return bool

    @property
    def _dflt_view_value(self):
        return False


@dataclass
class NumberInputBase(InputBase):
    """Base of numeric inputs, with an optional display ``format``."""

    format: str = None


@dataclass
class IntInputBase(NumberInputBase):
    """Integer input with optional bounds; values are cast with ``int``, defaulting to 0."""

    min_value: int = None
    max_value: int = None

    @property
    def _type(self):
        return int

    @property
    def _dflt_view_value(self):
        return 0


@dataclass
class FloatInputBase(NumberInputBase):
    """Float input with optional bounds and ``step``; values are cast with ``float``, defaulting to 0.0."""

    min_value: float = None
    max_value: float = None
    step: float = None

    @property
    def _type(self):
        return float

    @property
    def _dflt_view_value(self):
        return 0.0


@dataclass
class FileUploaderBase(InputBase):
    """File upload input, restricted to the given file ``type`` (extension(s)) if any."""

    type: str | list[str] | None = None
    accept_multiple_files: bool = False


SELECT_BOX_DFLT_INDEX = 0


@dataclass
class SelectorBase(InputBase):
    """Input choosing one value among ``options`` (a sequence, or a callable returning one).

    If no options are given and the parameter is annotated with a ``Literal``, the
    literal's values are the options.
    """

    options: Sequence | Callable = None

    def pre_render(self):
        """Resolve the options and pre-select the current view value (or the first option)."""
        self.options = self.options or []
        options = self._ensure_options()
        if not options:
            annot = self.obj.annotation
            if get_origin(annot) == Literal:
                options = list(get_args(annot))
        self._options = list(options)
        if self._options:
            self._preselected_index = (
                self._options.index(self.view_value)
                if self.view_value in self._options
                else SELECT_BOX_DFLT_INDEX
            )
            selected_value = self._options[self._preselected_index]
            if selected_value != self.view_value:
                self.view_value = selected_value
            if self.on_value_change:
                self.on_value_change(selected_value)

    @property
    def _dflt_view_value(self):
        options = self._ensure_options()
        return options[SELECT_BOX_DFLT_INDEX] if options else None

    def _ensure_options(self) -> Sequence:
        return self.options() if callable(self.options) else self.options


@dataclass
class KwargsInputBase(InputBase):
    """Input for a ``**kwargs`` parameter, with one sub-input per name in ``func_sig``."""

    inputs: dict = None
    func_sig: Sig | Callable = None

    def pre_render(self):
        """Make ``self.get_kwargs``, a function with signature ``func_sig`` returning its kwargs."""
        super().pre_render()
        func_sig = self.func_sig if isinstance(self.func_sig, Sig) else self.func_sig()
        func_sig = func_sig or Sig()

        @func_sig
        def get_kwargs(**kwargs):
            return kwargs

        self.get_kwargs = get_kwargs

    def _return_kwargs(self, output):
        self.value.set(output)
