
class GemToolMixIn( object ):
    def getDeps( self ) :
        return [ 'gem', 'ruby' ]
    
    def _gemName( self ):
        return self._name
        
    def _installTool( self, env ):
        puppet_ver = env.get(self._name + 'Ver', None)
        version_arg = []
        
        if puppet_ver:
            version_arg = ['--version', puppet_ver]

        self._callExternal( [ env['gemBin'], 'install', self._gemName() ] + env['gemInstallArgs'] + version_arg )
        
    def updateTool( self, env ):
        if env.get(self._name + 'Ver', None) :
            self._installTool( self, env )
        else :
            self._callExternal( [ env['gemBin'], 'update', self._gemName() ] + env['gemInstallArgs'] )
        
    def uninstallTool( self, env ):
        self._callExternal( [ env['gemBin'], 'uninstall', self._gemName() ] )
        self._have_tool = False
