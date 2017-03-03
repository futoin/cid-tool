
import os

from ..buildtool import BuildTool

class pipTool( BuildTool ):
    REQUIREMENTS_FILE = 'requirements.txt'

    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ self.REQUIREMENTS_FILE ]
        )
    
    def getDeps( self ) :
        return [ 'python', 'venv' ]
    
    def _installTool( self, env ):
        # make sure we install better up-to-date pip
        self._callExternal([
            os.path.join( env['venvDir'], 'bin', 'easy_install' ), 'pip'
        ])

    def updateTool( self, env ):
        self._callExternal( [ env['pipBin'], 'install', '-q', '--upgrade', 'pip' ] )
        
    def uninstallTool( self, env ):
        pass
    
    def initEnv( self, env ) :
        pipBin = os.path.join( env['venvDir'], 'bin', 'pip' )
        pipBin = env.setdefault( 'pipBin', pipBin )
        self._have_tool = os.path.exists( pipBin )
    
    def onPrepare( self, config ):
        if os.path.exists(self.REQUIREMENTS_FILE):
            self._callExternal( [ config['env']['pipBin'], 'install', '-r', self.REQUIREMENTS_FILE ] )
