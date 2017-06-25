
import os

from ..buildtool import BuildTool
from .piptoolmixin import PipToolMixIn


class cidTool(PipToolMixIn, BuildTool):
    "Noop FutoIn-CID - a workaround to allow CID use from virtualenv"

    def _pipName(self):
        return 'futoin-cid'

    def _installTool(self, env):
        try:
            self._callExternal(
                [env['pipBin'], 'install', '-q', '-e', os.environ['CID_SOURCE_DIR']])
        except KeyError:
            PipToolMixIn._installTool(self, env)
