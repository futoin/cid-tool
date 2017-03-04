
import os, re

from ..buildtool import BuildTool

class releaseTool( BuildTool ):
    "FutoIn CID-specific release processing"
    
    RELEASE_FILE = os.path.join('futoin', 'cid', '__init__.py')

    def autoDetect( self, config ) :
        return True

    def updateProjectConfig( self, config, updates ) :
        def updater( content ):
            if 'version' in updates:
                return re.sub(
                    r'^.*__version__.*$',
                    '__version__ = \'{0}\''.format(updates['version']),
                    content,
                    flags=re.MULTILINE
                )
        return self._updateTextFile(
            self.RELEASE_FILE,
            updater
        )

    def initEnv( self, env ):
        self._have_tool = True
