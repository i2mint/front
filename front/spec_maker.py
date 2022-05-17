from front.types import FrontSpec, Map
from front.util import deep_merge, normalize_map


class SpecMaker:
    def mk_spec(self, config: Map, convention: Map) -> FrontSpec:

        config = normalize_map(config)
        convention = normalize_map(convention)

        # def get_obj_rendering_convention(obj):
        #     for k, v in rendering_convention.items():
        #         if isinstance(obj, k):
        #             return v
        #     return {}

        # rendering_spec = {}
        # rendering_convention = convention.get('rendering', {})
        # for obj in objs:
        #     obj_rendering_config = config.get(obj, {}).get('rendering', {})
        #     obj_rendering_convention = get_obj_rendering_convention(obj)
        #     rendering_spec[obj] = deep_merge(
        #         obj_rendering_convention,
        #         obj_rendering_config
        #     )
        # return FrontSpec(
        #     obj_spec={},
        #     rendering_spec=rendering_spec,
        #     app_spec={},
        # )

        spec = deep_merge(convention, config)
        return FrontSpec(
            obj_spec=spec.get('obj', {}),
            rendering_spec=spec.get('rendering', {}),
            app_spec=spec.get('app', {}),
        )
