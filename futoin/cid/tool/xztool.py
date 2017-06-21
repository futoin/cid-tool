
from ..runenvtool import RunEnvTool


class xzTool(RunEnvTool):
    """Free general-purpose data compression software with a high compression ratio.

Home: https://tukaani.org/xz/
"""

    def _installTool(self, env):
        self._requirePackages(['xz-utils'])
        self._requireEmerge(['app-arch/xz-utils'])
        self._requirePacman(['xz-utils'])
        self._requireApk(['xz'])
