
from __future__ import print_function, absolute_import


class VersionMixIn(object):
    """
CID tools are required to ignore bug-fix/patch release
version parts and always install the latest from release line.
"""

    def getVersionParts(self):
        """Override, if tool has different number of meaningful parts"""
        return 2

    def sanitizeVersion(self, env):
        """Should be called implicitly by standard CID functionality"""
        ver_var = self._name + 'Ver'
        ver = env.get(ver_var, None)

        if ver:
            end = self.getVersionParts()
            new_ver = ver.split('.')[:end]
            new_ver = '.'.join(new_ver)

            if env[ver_var] != new_ver:
                self._warn('Too precise version "{0}" for "{1}" - trimmed to "{2}"'
                           .format(ver, self._name, new_ver))
                env[ver_var] = new_ver
