from typing import Callable
from i2 import Sig


def implement_component(
    base_cls: type,
    component_factory: Callable,
    input_value_callback: Callable = None,
    **input_mapping
):
    component_factory_sig = Sig(component_factory)
    keyword_names = component_factory_sig.keyword_names

    class component_class(base_cls):
        def render(self):
            component_factory_kwargs = {}
            for name in keyword_names:
                attr_name = input_mapping.get(name, name)
                attr = getattr(self, attr_name, None)
                if attr is not None:
                    component_factory_kwargs[name] = attr
            input_value = component_factory(**component_factory_kwargs)
            if input_value_callback:
                input_value_callback(input_value, self)
            return input_value

    return component_class
