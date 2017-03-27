
from ..runenvtool import RunEnvTool

class unzipTool( RunEnvTool ):
    def _installTool( self, env ):
        self._requirePackages(['unzip'])
        self._requireEmerge(['app-arch/unzip'])
        self._requirePacman(['unzip'])
