
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
            self._callExternal( [ scpBin, '-Bq', package, dst ] )
        else :
            package_basename = os.path.basename( package )
            src = '{0}/{1}'.format( config['rmsRepo'], package )
            dst = '{0}/{1}/{2}'.format( config['rmsRepo'], rms_pool, package_basename )

            self._callExternal( [ scpBin, '-Bq', src, package_basename ] )
            self.rmsVerifyHash( config, package_basename )

            # Note: promotion must no re-upload an artifact to avoid
            # risk of modifications
            self._callExternal( [ scpBin, '-Bq', src, dst ] )
