
import os, re

from ..buildtool import BuildTool

class releaseTool( BuildTool ):
    "FutoIn CID-specific release processing"

    def updateProjectConfig( self, config, updates ) :
        def updater( content ):
            if 'version' in updates:
                return re.sub(
                    '^.*__version__.*$',
                    '__version__=\'{0}\''.format(updates['version']),
                    content,
                    flags=re.MULTILINE
                )
        return self._updateTextFile(
            os.path.join('futoin', 'cid', '__init__.py'),
            updater
        )
