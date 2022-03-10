"""Base functions for front dispatching"""

from functools import partial
from typing import Mapping, Optional
from i2 import double_up_as_factory

from front.util import inject_enum_annotations, subdict
from front.crude import (
    keys_to_values_if_non_mapping_iterable,
    prepare_for_crude_dispatch,
)


# Note: Could also use a Pipe to make the dispatcher (more composable?)
# Note: Should evolve to a parametrized pipeline of preparers.
@double_up_as_factory
def prepare_for_dispatch(
    func=None,
    *,
    # for prepare_for_crude_dispatch
    param_to_mall_map=(),
    mall=None,
    output_store=None,
    save_name_param: str = 'save_name',
    include_stores_attribute: bool = False,
    # for setting defaults
    defaults: Optional[Mapping] = None,
):
    param_to_mall_map = keys_to_values_if_non_mapping_iterable(param_to_mall_map)

    from i2 import Sig

    wrapped_func = func  # to seed the following sequence of wrapping

    # crude wrap
    wrapped_func = prepare_for_crude_dispatch(
        wrapped_func,
        param_to_mall_map=param_to_mall_map,
        mall=mall,
        output_store=output_store,
        save_name_param=save_name_param,
        include_stores_attribute=include_stores_attribute,
    )

    # enum wrap
    wrapped_func = inject_enum_annotations(
        wrapped_func,
        extract_enum_value=True,
        **{param: mall[mall_key] for param, mall_key in param_to_mall_map.items()},
    )

    # insert defaults
    if defaults:
        # get only keys that are in wrapped_func signature as well as defaults
        wrapped_sig = Sig(wrapped_func)
        _defaults = wrapped_sig.kwargs_from_args_and_kwargs(
            (), defaults or {}, allow_partial=True, allow_excess=True
        )
        _defaults_args, _defaults_kwargs = wrapped_sig.args_and_kwargs_from_kwargs(
            _defaults, allow_partial=True, allow_excess=True
        )
        wrapped_func = partial(wrapped_func, *_defaults_args, **_defaults_kwargs)

    return wrapped_func
