
from .ondemand import OnDemandMixIn


class DataSlots(OnDemandMixIn):
    __slots__ = (
        '_startup_env',
        '_env',
        '_config',
        '_overrides',
        '_global_config',
        '_user_config',
        '_deploy_config',
        '_project_config',

        '_current_dir',
        '_devserve_mode',

        '_deploy_lock',
        '_master_lock',
        '_global_lock',

        '_tool_impl',

        '_lastPackages',
    )
