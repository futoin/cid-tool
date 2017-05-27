
from .subtool import SubTool

import os
import signal

__all__ = ['RuntimeTool']


class RuntimeTool(SubTool):
    DEFAULT_EXIT_TIMEOUT = 5000

    def onRun(self, config, file, args, tune):
        env = config['env']
        self._callInteractive([
            env[self._name + 'Bin'], file
        ] + args)

    def tuneDefaults(self):
        return {
            'minMemory': '1M',
            'connMemory': '1M',
            'scalable': False,
            'reloadable': False,
            'exitTimeoutMS': self.DEFAULT_EXIT_TIMEOUT,
        }

    def onStop(self, config, pid, tune):
        self._signalPID(pid, signal.SIGTERM)

    def onReload(self, config, pid, tune):
        if tune['reloadable']:
            self._signalPID(pid, signal.SIGHUP)
        else:
            self.onStop(config, pid, tune)

    def _signalPID(self, pid, sig):
        os.kill(pid, sig)
