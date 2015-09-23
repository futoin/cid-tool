
from citool.subtool import SubTool

class scpTool( SubTool ):
    def getType( self ):
        return self.TYPE_RMS

    def rmsPromote( self, config, package, rms_pool ) :
        scpBin = config['env']['scpBin']
        dst = '{0}/{1}/{2}'.format( config['rmsRepo'], rms_pool, package )
        self._callExternal( [ scpBin, package, dst ] )
