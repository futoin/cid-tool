
import signal

from ..runtimetool import RuntimeTool
from .gemtoolmixin import GemToolMixIn


class pumaTool(GemToolMixIn, RuntimeTool):
    """A ruby web server built for concurrency http://puma.io
"""
    _SIG_RELOAD = signal.SIGUSR2

    def tuneDefaults(self):
        return {
            'minMemory': '8M',
            'connMemory': '4M',
            'connFD': 8,
            'socketTypes': ['unix', 'tcp'],
            'socketType': 'unix',
            'socketProtocol': 'http',
            'scalable': True,
            'reloadable': True,
            'multiCore': False,  # use workers on service level
            'maxRequestSize': '1M',
        }

    def onRun(self, config, svc, args):
        svc_tune = svc['tune']

        #---

        if svc_tune['socketType'] == 'unix':
            socket = 'unix://{0}'.format(svc_tune['socketPath'])
        else:
            socket = 'tcp://{0}:{1}'.format(
                svc_tune['socketAddress'], svc_tune['socketPort'])

        if config['env']['type'] == 'dev':
            ruby_env = 'development'
        else:
            ruby_env = 'production'

        #---
        heap_limit = self._parseMemory(svc_tune['maxMemory'])
        heap_limit = int(heap_limit // 1024 // 1024)

        threads = svc_tune['maxConnections']

        puma_args = [
            '-b', socket,
            '-e', ruby_env,
            '-t', '{0}:{0}'.format(threads)
        ]

        #---

        cmd = [
            config['env']['pumaBin'],
            svc['path']
        ] + puma_args + args

        self._callInteractive(cmd)
