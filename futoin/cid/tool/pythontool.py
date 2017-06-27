
from __future__ import print_function

import os

from ..runtimetool import RuntimeTool


class pythonTool(RuntimeTool):
    """Python is a programming language.

Home: https://www.python.org/

Only the first part of pythonVer is used for installation of
system packages OS-specific way.
"""
    VER_CMD = 'import sys; print( "%s.%s" % (sys.version_info.major, sys.version_info.minor) )'

    def getPostDeps(self):
        # hackish hack
        return ['virtualenv']

    def envNames(self):
        return ['pythonBin', 'pythonVer']

    def _installTool(self, env):
        if int(env['pythonVer'].split('.')[0]) == 3:
            self._requireDeb(['python3'])
            self._requireZypper(['python3'])

            self._requireYumEPEL()
            self._requireYum(['python34'])
            self._requirePacman(['python'])
            self._requireApk('python3')
            self._requireBrew('python3')
        else:
            self._requirePackages(['python'])
            self._requirePacman(['python2'])
            self._requireApk('python2')
            self._requireBrew('python')

        self._requireEmerge(['=dev-lang/python-{0}*'.format(env['pythonVer'])])

    def uninstallTool(self, env):
        pass

    def initEnv(self, env):
        python_ver = env.setdefault('pythonVer', '3')
        bin_name = None

        if self._isGentoo():
            if len(python_ver) == 3:
                os.environ['EPYTHON'] = 'python{0}'.format(python_ver)
            elif int(python_ver.split('.')[0]) == 3:
                os.environ['EPYTHON'] = 'python3.4'
            else:
                os.environ['EPYTHON'] = 'python2.7'
        elif self._isArchLinux():
            if int(python_ver.split('.')[0]) == 2:
                bin_name = 'python2'
        elif int(python_ver.split('.')[0]) == 3:
            bin_name = 'python3'

        super(pythonTool, self).initEnv(env, bin_name)

        if self._have_tool and 'pythonRawBin' not in env:
            env['pythonRawBin'] = env['pythonBin']
            python_ver_fact = self._callExternal(
                [env['pythonRawBin'], '-c', self.VER_CMD],
                verbose=False
            ).strip()

            if python_ver.split('.') > python_ver_fact.split('.'):
                self._errorExit(
                    'Too old python version "{0}" when "{1}" is required'
                    .format(python_ver, python_ver_fact)
                )

            env['pythonFactVer'] = python_ver_fact

    def tuneDefaults(self):
        return {
            'minMemory': '8M',
            'socketType': 'none',
            'scalable': False,
        }
