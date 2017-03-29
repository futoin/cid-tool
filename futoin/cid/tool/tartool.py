
from ..runenvtool import RunEnvTool

class tarTool( RunEnvTool ):
    """The GNU version of the tar archiving utility.
"""    
    def _installTool( self, env ):
        self._requirePackages(['tar'])
        self._requireEmerge(['app-arch/tar'])
        self._requirePacman(['tar'])
