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

from ..runtimetool import RuntimeTool


class pythonTool(RuntimeTool):
    """Python is a programming language.

Home: https://www.python.org/

Only the first part of pythonVer is used for installation of
system packages OS-specific way.
"""
    __slots__ = ()

    VER_CMD = 'import sys; print( "%s.%s" % (sys.version_info.major, sys.version_info.minor) )'

    def getPostDeps(self):
        # hackish hack
        return ['virtualenv']

    def envNames(self):
        return ['pythonBin', 'pythonVer']

    def _installTool(self, env):
        if int(env['pythonVer'].split('.')[0]) == 3:
            self._install.deb(['python3'])
            self._install.zypper(['python3'])

            self._install.yumEPEL()
            self._install.yum(['python34'])
            self._install.pacman(['python'])
            self._install.apk('python3')
            self._install.brew('python3')
        else:
            self._install.debrpm(['python'])
            self._install.pacman(['python2'])
            self._install.apk('python2')
            self._install.brew('python')

        self._install.emerge(
            ['=dev-lang/python-{0}*'.format(env['pythonVer'])])

    def uninstallTool(self, env):
        pass

    def initEnv(self, env):
        environ = self._environ
        detect = self._detect

        python_ver = env.setdefault('pythonVer', '3')
        bin_name = None

        if detect.isGentoo():
            if len(python_ver) == 3:
                environ['EPYTHON'] = 'python{0}'.format(python_ver)
            elif int(python_ver.split('.')[0]) == 3:
                environ['EPYTHON'] = 'python3.4'
            else:
                environ['EPYTHON'] = 'python2.7'
        elif detect.isArchLinux():
            if int(python_ver.split('.')[0]) == 2:
                bin_name = 'python2'
        elif int(python_ver.split('.')[0]) == 3:
            bin_name = 'python3'

        super(pythonTool, self).initEnv(env, bin_name)

        if self._have_tool and 'pythonRawBin' not in env:
            env['pythonRawBin'] = env['pythonBin']
            python_ver_fact = self._executil.callExternal(
                [env['pythonRawBin'], '-c', self.VER_CMD],
                verbose=False
            ).strip()

            if python_ver.split('.') > python_ver_fact.split('.'):
                self._errorExit(
                    'Too old python version "{0}" when "{1}" is required'
                    .format(python_ver, python_ver_fact)
                )

            env['pythonFactVer'] = python_ver_fact

    def tuneDefaults(self, env):
        return {
            'minMemory': '8M',
            'socketType': 'none',
            'scalable': False,
            'reloadable': False,
            'multiCore': True,
        }
