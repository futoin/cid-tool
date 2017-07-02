
from .ondemand import OnDemandMixIn


class DataSlots(OnDemandMixIn):
    __slots__ = (
        # ConfigMixIn
        '_startup_env',
        '_env',
        '_config',
        '_overrides',
        '_global_config',
        '_user_config',
        '_deploy_config',
        '_project_config',

        # DeployMixIn
        '_current_dir',
        '_devserve_mode',

        # LockMixIn
        '_deploy_lock',
        '_master_lock',
        '_global_lock',

        # ToolMixIn
        '_tool_impl',

        '_lastPackages',

        # ServiceMixIn
        '_running',
        '_reload_services',
        '_interruptable',
    )

    _FUTOIN_JSON = 'futoin.json'
