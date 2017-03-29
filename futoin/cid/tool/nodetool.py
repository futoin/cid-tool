
import os

from ..runtimetool import RuntimeTool
from .bashtoolmixin import BashToolMixIn

class nodeTool( BashToolMixIn, RuntimeTool ):
    """Node.js is a JavaScript runtime built on Chrome's V8 JavaScript engine.
    
Home: https://nodejs.org/en/    
"""
    def getDeps( self ) :
        return [ 'nvm', 'bash' ]

    def _installTool( self, env ):
        self._callBash( env,
                'source {0} --no-use && nvm install {1}'
                .format(env['nvmInit'], env['nodeVer']))
            
    def updateTool( self, env ):
        self._installTool( env )
        
    def uninstallTool( self, env ):
        self._callBash( env,
              'source {0} --no-use && nvm deactivate && nvm uninstall {1}'
              .format(env['nvmInit'], env['nodeVer']) )
        self._have_tool = False

    def envNames( self ) :
        return ['nodeBin', 'nodeVer']
    
    def initEnv( self, env ) :
        node_version = env.setdefault('nodeVer', 'stable')

        try:
            env_to_set = self._callBash( env,
                'source {0} --no-use && \
                nvm use {1} >/dev/null && \
                env | egrep "(NVM_|\.nvm)"'
                .format(env['nvmInit'], node_version),
                verbose = False
            )
        except:
            return

        if env_to_set :
            self._updateEnvFromOutput(env_to_set)
            super(nodeTool, self).initEnv( env )
