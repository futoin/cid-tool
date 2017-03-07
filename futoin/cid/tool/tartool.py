
from ..runenvtool import RunEnvTool

class tarTool( RunEnvTool ):
    def _installTool( self, env ):
        self._requirePackages(['tar'])
        self._requireEmerge(['app-arch/tar'])
        self._requirePacman(['tar'])
