
from ..runenvtool import RunEnvTool

class zipTool( RunEnvTool ):
    def _installTool( self, env ):
        self._requirePackages(['zip'])
        self._requireEmerge(['app-arch/zip'])
        self._requirePacman(['zip'])
