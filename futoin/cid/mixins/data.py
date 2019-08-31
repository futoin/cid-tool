#
# Copyright 2015-2019 Andrey Galkin <andrey@futoin.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

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
    _FUTOIN_USER_JSON = '.futoin.json'
    _FUTOIN_MERGED_JSON = '.futoin.merged.json'

    _DEPLOY_LOCK_FILE = '.futoin-deploy.lock'
    _MASTER_LOCK_FILE = '.futoin-master.lock'
    _GLOBAL_LOCK_FILE = '.futoin-global.lock'
