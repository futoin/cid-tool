
from ..buildtool import BuildTool

class dockercomposeTool( BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'docker-compose.yml' ]
        )
    
    def getDeps( self ) :
        return [ 'pip' ]
        
    def _installTool( self, env ):
        if int(env['pythonVer'].split('.')[0]) == 3:
            self._requireDeb(['python3-dev'])
            self._requireZypper(['python3-devel'])
            self._requireYum(['epel-release'])
            self._requireYum(['python34-devel'])
        else:
            self._requireDeb(['python-dev'])
            self._requireZypper(['python-devel'])
            self._requireYum(['epel-release'])
            self._requireYum(['python-devel'])

        self._callExternal( [ env['pipBin'], 'install', '-q', 'docker-compose' ] )
        
    def updateTool( self, env ):
        self._callExternal( [ env['pipBin'], 'install', '-q', '--upgrade', 'docker-compose' ] )
        
    def uninstallTool( self, env ):
        self._callExternal( [ env['pipBin'], 'uninstall', '-q', 'bundler' ] )
        self._have_tool = False

    def onBuild( self, config ):
        self._callExternal( [ config['env']['dockercomposeBin'], 'build' ] )
        
    def initEnv( self, env ) :
        super(dockercomposeTool, self).initEnv( env, 'docker-compose' )
