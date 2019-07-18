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

from ..runenvtool import RunEnvTool


class brewTool(RunEnvTool):
    """Homebrew. The missing package manager for macOS.

Home: https://brew.sh/

brewInstall is use for admin user installation.
brewDir & brewGit is used for local install.

Hint: Unprivileged brew does not work well with many bottles, you may want to use
    brewSudo='/usr/bin/sudo -n -H -u adminaccount' with "cid sudoers" config.
"""
    __slots__ = ()

    _MACOS_ADMIN_GID = 80  # dirty hack for now
    _GLOBAL_BREW_DIR = '/usr/local'

    def envNames(self):
        return ['brewBin', 'brewDir', 'brewGit', 'brewInstall', 'brewSudo']

    def _installTool(self, env):
        if self._isLocalBrew(env):
            self._warn(
                'Unprivileged Homebrew install has many drawbacks. Check "cid tool describe brew"')
            homebrew_git = env['brewGit']
            homebrew_dir = env['brewDir']

            git = self._pathutil.which('git')

            if not git:
                xcode_select = self._pathutil.which('xcode-select')
                self._executil.callExternal(
                    [xcode_select, '--install'], suppress_fail=True)
                git = self._pathutil.which('git')

            self._executil.callExternal(
                [git, 'clone', homebrew_git, homebrew_dir])
        else:
            # should be system-available
            curl = self._pathutil.which('curl')
            ruby = self._pathutil.which('ruby')
            homebrew_install = env['brewInstall']

            curl_args = self._configutil.timeouts(env, 'curl')

            brew_installer = self._executil.callExternal(
                [curl, '-fsSL', homebrew_install] + curl_args
            )

            self._executil.callExternal([ruby, '-'], input=brew_installer)

    def _isLocalBrew(self, env):
        return env['brewDir'] != self._GLOBAL_BREW_DIR

        if self._MACOS_ADMIN_GID not in self._os.getgroups():
            return True

        return False

    def initEnv(self, env, bin_name=None):
        ospath = self._ospath
        os = self._os
        brewSudo = env.get('brewSudo', '')

        if self._MACOS_ADMIN_GID not in os.getgroups() and not brewSudo:
            homebrew_dir = ospath.join(self._environ['HOME'], '.homebrew')
            env.setdefault('brewDir', homebrew_dir)
        else:
            env.setdefault('brewDir', self._GLOBAL_BREW_DIR)

            if brewSudo:
                self._environ['brewSudo'] = brewSudo

        self._environ['HOMEBREW_NO_GITHUB_API'] = '1'
        env.setdefault('brewGit',
                       'https://github.com/Homebrew/brew.git')
        env.setdefault('brewInstall',
                       'https://raw.githubusercontent.com/Homebrew/install/master/install')

        if self._isLocalBrew(env):
            homebrew_dir = env['brewDir']
            bin_dir = ospath.join(homebrew_dir, 'bin')
            brew = ospath.join(bin_dir, 'brew')

            if ospath.exists(brew):
                self._pathutil.addBinPath(bin_dir, True)
                env['brewBin'] = brew
                self._have_tool = True
        else:
            env.setdefault('brewDir', self._GLOBAL_BREW_DIR)
            super(brewTool, self).initEnv(env, bin_name)
