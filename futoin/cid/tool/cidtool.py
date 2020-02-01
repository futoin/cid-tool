#
# Copyright 2015-2020 Andrey Galkin <andrey@futoin.org>
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

from .. import __version__ as _version
from ..buildtool import BuildTool
from .piptoolmixin import PipToolMixIn

_PROXY_BIN_TPL = """#!/bin/sh
exec {0} -m{1} "$@"
"""


class cidTool(BuildTool):
    "Noop FutoIn-CID - a workaround to allow CID use from virtualenv"

    __slots__ = ()

    def envNames(self):
        return ['cidVer']

    def getDeps(self):
        return ['pip', 'virtualenv']

    def _pipName(self):
        return 'futoin-cid'

    def _callPip(self, cmd, args):
        ext = self._ext
        os = ext.os
        need_sudo = False

        if ext.detect.isAdmin():
            user_args = ['--system']
        elif os.stat(__file__).st_uid != os.geteuid():
            user_args = ['--system']
            need_sudo = True
        else:
            user_args = ['--user']

        if cmd == 'uninstall':
            user_args = []

        cmd_args = [ext.sys.executable, '-mpip', cmd] + user_args + args

        if need_sudo:
            self._executil.trySudoCall(cmd_args)
        else:
            self._executil.callExternal(cmd_args, use_orig_env=True)

    def _installTool(self, env):
        source_dir = self._environ.get('CID_SOURCE_DIR', None)

        if source_dir:
            self._callPip('install', ['-q', '-e', source_dir])
        else:
            self._callPip('install', ['-q', '--upgrade', self._pipName()])

    def _updateTool(self, env):
        self._installTool(env)

    def uninstallTool(self, env):
        self._callPip('uninstall', ['-q', '--yes', self._pipName()])
        self._have_tool = False

    def initEnv(self, env, bin_name=None):
        os = self._os
        ospath = self._ospath
        pathutil = self._pathutil
        sys = self._sys
        stat = self._ext.stat

        # Dirty hack, so proxy script deactives virtualenv
        venvDir = env['virtualenvDir']

        cli_bin = ospath.join(venvDir, 'bin', 'cid')
        cli_cmd = _PROXY_BIN_TPL.format(sys.executable, 'futoin.cid')
        cte_bin = ospath.join(venvDir, 'bin', 'cte')
        cte_cmd = _PROXY_BIN_TPL.format(sys.executable, 'futoin.cid.cte')
        fperm = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH

        if (not ospath.exists(cli_bin)) or os.stat(cli_bin).st_uid == os.geteuid():
            pathutil.checkUpdateTextFile(cli_bin, lambda _: cli_cmd)
            os.chmod(cli_bin, fperm)

        if (not ospath.exists(cte_bin)) or os.stat(cte_bin).st_uid == os.geteuid():
            pathutil.checkUpdateTextFile(cte_bin, lambda _: cte_cmd)
            os.chmod(cte_bin, fperm)

        # Handle version check
        ver = env.get('cidVer', _version)
        vers = [_version, ver]
        self._versionutil.sort(vers)
        self._have_tool = vers[0] == ver
