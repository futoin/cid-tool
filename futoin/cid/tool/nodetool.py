
import os

from ..runtimetool import RuntimeTool
from .bashtoolmixin import BashToolMixIn

class nodeTool( BashToolMixIn, RuntimeTool ):
    def getDeps( self ) :
        return [ 'nvm', 'bash' ]

    def _installTool( self, env ):
        nvm_dir = env['nvmDir']
        node_version = env['nodeVer']
        self._callBash( env,
                'source {0}/nvm.sh --no-use && nvm install {1}'
                .format(nvm_dir, node_version))
            
    def updateTool( self, env ):
        self._installTool( env )
        
    def uninstallTool( self, env ):
        nvm_dir = env['nvmDir']
        node_version = env['nodeVer']
        self._callBash( env,
              'source {0}/nvm.sh --no-use && nvm deactivate && nvm uninstall {1}'
              .format(nvm_dir, node_version) )
        self._have_tool = False

    def _envNames( self ) :
        return ['nodeBin', 'nodeVer']
    
    def initEnv( self, env ) :
        node_version = env.setdefault('nodeVer', 'stable')

        nvm_dir = env['nvmDir']

        try:
            env_to_set = self._callBash( env,
                'source {0}/nvm.sh --no-use && \
                nvm use {1} >/dev/null && \
                env | egrep "(NVM_|\.nvm)"'.format(nvm_dir, node_version),
                verbose = False
            )
        except:
            return

        if env_to_set :
            self._updateEnvFromOutput(env_to_set)
            super(nodeTool, self).initEnv( env )
