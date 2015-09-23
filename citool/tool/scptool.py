
from citool.subtool import SubTool
import os

class scpTool( SubTool ):
    def getType( self ):
        return self.TYPE_RMS

    def rmsPromote( self, config, package, rms_pool ) :
        scpBin = config['env']['scpBin']
        
        if os.path.exists( package ) :
            dst = '{0}/{1}/{2}'.format(
                    config['rmsRepo'],
                    rms_pool, package )
            self._callExternal( [ scpBin, package, dst ] )
        else :
            src = '{0}/{1}'.format( config['rmsRepo'], package )
            dst = '{0}/{1}/{2}'.format(
                    config['rmsRepo'],
                    rms_pool, os.path.basename( package ) )
            self._callExternal( [ scpBin, src, dst ] )
