
from ..runenvtool import RunEnvTool

class unzipTool( RunEnvTool ):
    """list, test and extract compressed files in a ZIP archive.
"""
    def _installTool( self, env ):
        self._requirePackages(['unzip'])
        self._requireEmerge(['app-arch/unzip'])
        self._requirePacman(['unzip'])
