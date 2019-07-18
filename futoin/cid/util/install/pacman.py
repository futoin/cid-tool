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

from ...mixins.ondemand import ext as _ext

_pacman = _ext.pathutil.which('pacman')


def pacman(packages):
    if _pacman:
        packages = _ext.configutil.listify(packages)

        _ext.executil.trySudoCall(
            [_pacman, '-S', '--noconfirm', '--needed'] + packages,
            errmsg='you may need to install the build deps manually !'
        )
