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

from .subtool import SubTool

__all__ = ['RuntimeTool']


class RuntimeTool(SubTool):
    __slots__ = ()
    DEFAULT_EXIT_TIMEOUT = 5000

    def __init__(self, name):
        super(RuntimeTool, self).__init__(name)

    def onRun(self, config, svc, args):
        env = config['env']
        self._executil.callInteractive([
            env[self._name + 'Bin'], svc['path']
        ] + args)

    def tuneDefaults(self, env):
        return {
            'minMemory': '1M',
            'connMemory': '1M',
            'scalable': False,
            'reloadable': False,
            'multiCore': False,
            'exitTimeoutMS': self.DEFAULT_EXIT_TIMEOUT,
            'maxRequestSize': '1M',
            'socketProtocol': 'custom',
        }

    def onStop(self, config, pid, tune):
        self._signalPID(pid, self._sigStop())

    def onReload(self, config, pid, tune):
        if tune['reloadable']:
            self._signalPID(pid, self._sigReload())
        else:
            self.onStop(config, pid, tune)

    def onPreConfigure(self, config, runtime_dir, svc, cfg_svc_tune):
        pass

    def _signalPID(self, pid, sig):
        self._os.kill(pid, sig)

    def _sigReload(self):
        return self._ext.signal.SIGHUP

    def _sigStop(self):
        return self._ext.signal.SIGTERM
