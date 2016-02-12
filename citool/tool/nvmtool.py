
from citool.subtool import SubTool
import subprocess
import os

class nvmTool( SubTool ):
    "Node Version Manager"
    def getType( self ):
        return self.TYPE_RUNENV

    def _installTool( self ):
        self._callExternal(
            [ 'bash', '-c',
              'test -d ~/.nvm || \
              git clone https://github.com/creationix/nvm.git ~/.nvm && \
              cd ~/.nvm && git checkout $(git describe --abbrev=0 --tags)' ] )
        self._callExternal(
            [ 'bash', '-c',
              'source ~/.nvm/nvm.sh && nvm install stable' ] )
            
    def initEnv( self, env ) :
        try:
            env_to_set = self._callExternal(
                [ 'bash', '-c',
                'source ~/.nvm/nvm.sh && \
                nvm use stable >/dev/null && \
                env | egrep "(NVM_|\.nvm)"' ],
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
        
        
