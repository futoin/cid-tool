
import os, re

from ..buildtool import BuildTool

class releaseTool( BuildTool ):
    "FutoIn CID-specific release processing"
    
    RELEASE_FILE = os.path.join('futoin', 'cid', '__init__.py')
    CHANGELOG_FILE = 'CHANGELOG.txt'

    def autoDetect( self, config ) :
        return True

    def updateProjectConfig( self, config, updates ) :
        def py_updater( content ):
            if 'version' in updates:
                return re.sub(
                    r'^.*__version__.*$',
                    '__version__ = \'{0}\''.format(updates['version']),
                    content,
                    flags=re.MULTILINE
                )
        def cl_updater( content ):
            if 'version' in updates:
                return re.sub(
                    r'^=== \(next\) ===$',
                    '=== {0} ==='.format(updates['version']),
                    content,
                    count = 1,
                    flags=re.MULTILINE
                )
        res = self._updateTextFile(
            self.RELEASE_FILE,
            py_updater
        )
        res += self._updateTextFile(
            self.CHANGELOG_FILE,
            cl_updater
        )
        return res

    def initEnv( self, env ):
        self._have_tool = True
