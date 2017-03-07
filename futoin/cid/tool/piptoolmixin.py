
class PipToolMixIn( object ):
    def getDeps( self ) :
        return [ 'pip' ]

    def _pipName( self ):
        return self._name

    def _installTool( self, env ):
        self._callExternal( [ env['pipBin'], 'install', '-q', self._pipName() ] )
        
    def updateTool( self, env ):
        self._callExternal( [ env['pipBin'], 'install', '-q', '--upgrade', self._pipName() ] )
        
    def uninstallTool( self, env ):
        self._callExternal( [ env['pipBin'], 'uninstall', '-q', self._pipName() ] )
        self._have_tool = False

    def _requirePythonDev( self, env ):
        if int(env['pythonVer'].split('.')[0]) == 3:
            self._requireDeb(['python3-dev'])
            self._requireZypper(['python3-devel'])
            self._requireYum(['epel-release'])
            self._requireYum(['python34-devel'])
            self._requirePacman(['python'])
        else:
            self._requireDeb(['python-dev'])
            self._requireZypper(['python-devel'])
            self._requireYum(['epel-release'])
            self._requireYum(['python-devel'])
            self._requirePacman(['python2'])
            
        self._requireEmergeDepsOnly(['dev-lang/python'])
        
    def _requirePip( self, env, package ):
        self._callExternal( [ env['pipBin'], 'install', '-q', package ] )