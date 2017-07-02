
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
