
from citool.subtool import SubTool

import os

class nodeTool( SubTool ):
    def getType( self ):
        return self.TYPE_RUNTIME
    
    def getDeps( self ) :
        return [ 'nvm', 'bash' ]

    def _installTool( self, env ):
        nvm_dir = env['nvmDir']
        node_version = env['nodeVer']
        bash_bin = env['bashBin']
        self._callExternal(
            [ bash_bin, '-c',
              'source {0}/nvm.sh && nvm install {1}'.format(nvm_dir, node_version) ] )
            
    def updateTool( self, env ):
        self._installTool( env )

    def initEnv( self, env ) :
        node_version = env.setdefault('nodeVer', 'stable')

        nvm_dir = env['nvmDir']
        bash_bin = env['bashBin']

        try:
            env_to_set = self._callExternal(
                [ bash_bin, '-c',
                'source {0}/nvm.sh && \
                nvm use {1} >/dev/null && \
                env | egrep "(NVM_|\.nvm)"'.format(nvm_dir, node_version) ],
                verbose = False
            )
        except:
            return

        if env_to_set :
            env_to_set = env_to_set.split( "\n" )

            for e in env_to_set:
                if not e: break
                n, v = e.split('=', 1)
                os.environ[n] = v

            self._have_tool = True
