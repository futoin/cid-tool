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
from .curltoolmixin import CurlToolMixIn


class jfrogTool(CurlToolMixIn, RunEnvTool):
    """JFrog: Command Line Interface for Artifactory and Bintray

Home: https://www.jfrog.com/confluence/display/CLI/JFrog+CLI
"""
    __slots__ = ()

    def _installTool(self, env):
        ospath = self._ospath
        os = self._os

        if self._detect.isMacOS():
            self._install.brew('jfrog-cli-go')
            return

        dst_dir = env['jfrogDir']
        get_url = env['jfrogGet']
        jfrog_bin = ospath.join(dst_dir, 'jfrog')

        if not ospath.exists(dst_dir):
            os.makedirs(dst_dir)

        self._callCurl(env, [get_url, '-o', jfrog_bin])
        stat = self._ext.stat
        os.chmod(jfrog_bin, stat.S_IRWXU | stat.S_IRGRP |
                 stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

    def _updateTool(self, env):
        if self._detect.isMacOS():
            return

        self.uninstallTool(env)
        self._installTool(env)

    def uninstallTool(self, env):
        if self._detect.isMacOS():
            return

        jfrog_bin = env['jfrogBin']
        if self._ospath.exists(jfrog_bin):
            self._os.remove(jfrog_bin)
        self._have_tool = False

    def envNames(self):
        return ['jfrogDir', 'jfrogBin', 'jfrogGet']

    def initEnv(self, env):
        bin_dir = env.setdefault('jfrogDir', env['binDir'])

        pkg = None
        url_base = 'https://api.bintray.com/content/jfrog/jfrog-cli-go/$latest'

        detect = self._detect

        if detect.isMacOS():
            pass
        elif detect.isAMD64():
            pkg = 'jfrog-cli-linux-amd64'
        else:
            pkg = 'jfrog-cli-linux-386'

        if pkg:
            env.setdefault(
                'jfrogGet',
                'https://api.bintray.com/content/jfrog/jfrog-cli-go/$latest/{0}/jfrog?bt_package={0}'.format(
                    pkg)
            )

        self._pathutil.addBinPath(bin_dir)

        super(jfrogTool, self).initEnv(env)

        if self._have_tool:
            env['jfrogDir'] = self._ospath.dirname(env['jfrogBin'])
