
from ..runenvtool import RunEnvTool


class zipTool(RunEnvTool):
    """package and compress (archive) files.
"""

    def _installTool(self, env):
        self._requirePackages(['zip'])
        self._requireEmerge(['app-arch/zip'])
        self._requirePacman(['zip'])
        self._requireApk(['zip'])
