
class NpmToolMixIn( object ):
    def getDeps( self ) :
        return [ 'node', 'npm' ]

    def _npmName( self ):
        return self._name
        
    def _installTool( self, env ):
        self._callExternal( [ env['npmBin'], 'install', '-g', self._npmName() ] )
        
    def updateTool( self, env ):
        self._callExternal( [ env['npmBin'], 'update', '-g', self._npmName() ] )
        
    def uninstallTool( self, env ):
        self._callExternal( [ env['npmBin'], 'uninstall', '-g', self._npmName() ] )
        self._have_tool = False
