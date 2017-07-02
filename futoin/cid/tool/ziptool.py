
from ..runenvtool import RunEnvTool


class zipTool(RunEnvTool):
    """package and compress (archive) files.
"""
    __slots__ = ()

    def _installTool(self, env):
        self._install.debrpm(['zip'])
        self._install.emerge(['app-arch/zip'])
        self._install.pacman(['zip'])
        self._install.apk(['zip'])
