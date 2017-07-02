
from ..buildtool import BuildTool
from .piptoolmixin import PipToolMixIn


class cidTool(PipToolMixIn, BuildTool):
    "Noop FutoIn-CID - a workaround to allow CID use from virtualenv"

    __slots__ = ()

    def _pipName(self):
        return 'futoin-cid'

    def _installTool(self, env):
        source_dir = self._environ.get('CID_SOURCE_DIR', None)

        if source_dir:
            self._executil.callExternal(
                [env['pipBin'], 'install', '-q', '-e', source_dir])
        else:
            PipToolMixIn._installTool(self, env)
