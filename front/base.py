"""Base functions for front dispatching"""

from functools import partial

from i2 import Pipe

from front.util import inject_enum_annotations
from front.crude import (
    keys_to_values_if_non_mapping_iterable,
    prepare_for_crude_dispatch,
)


def prepare_for_dispatch(
    func, param_to_mall_map=(), *, mall=None, output_store=None, defaults=()
):
    param_to_mall_map = keys_to_values_if_non_mapping_iterable(param_to_mall_map)

    # wrapper = Pipe(
    #     crude_dispatch=prepare_for_crude_dispatch(
    #         param_to_mall_map=param_to_mall_map,
    #         mall=mall,
    #         output_store=output_store,
    #     ),
    #     # enumify=inject_enum_annotations(
    #     #     **{param: mall[mall_key] for param, mall_key in param_to_mall_map.items()}
    #     # ),
    # )
    # wrapped_func = wrapper(func)

    wrapped_func = func

    wrapped_func = prepare_for_crude_dispatch(
        wrapped_func,
        param_to_mall_map=param_to_mall_map,
        mall=mall,
        output_store=output_store,
    )

    # TODO: When I add this, it breaks:
    wrapped_func = inject_enum_annotations(
        wrapped_func,
        extract_enum_value=True,
        **{param: mall[mall_key] for param, mall_key in param_to_mall_map.items()}
    )

    # extra, to get some defaults in:
    if defaults:
        wrapped_func = partial(wrapped_func, **dict(defaults))

    return wrapped_func
