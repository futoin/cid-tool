
from .subtool import SubTool

import os
import signal

__all__ = ['RuntimeTool']


class RuntimeTool(SubTool):
    DEFAULT_EXIT_TIMEOUT = 5000
    _SIG_STOP = signal.SIGTERM
    _SIG_RELOAD = signal.SIGHUP

    def onRun(self, config, svc, args):
        env = config['env']
        self._callInteractive([
            env[self._name + 'Bin'], svc['path']
        ] + args)

    def tuneDefaults(self):
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
        self._signalPID(pid, self._SIG_STOP)

    def onReload(self, config, pid, tune):
        if tune['reloadable']:
            self._signalPID(pid, self._SIG_RELOAD)
        else:
            self.onStop(config, pid, tune)

    def onPreConfigure(self, config, runtime_dir, svc, cfg_svc_tune):
        pass

    def _signalPID(self, pid, sig):
        os.kill(pid, sig)
