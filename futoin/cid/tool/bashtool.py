
from ..runenvtool import RunEnvTool
from ..runtimetool import RuntimeTool


class bashTool(RunEnvTool, RuntimeTool):
    """Bash is an sh-compatible command language interpreter.

Mostly used for internal purposes.
"""
    def tuneDefaults(self):
        return {
            'minMemory': '1M',
            'scalable': False,
            'reloadable': False,
            'multiCore': False,
            'exitTimeoutMS': self.DEFAULT_EXIT_TIMEOUT,
            'maxRequestSize': '1M',
            'socketProtocol': 'custom',
        }
