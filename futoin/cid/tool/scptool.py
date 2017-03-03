
import os
import re

from ..rmstool import RmsTool

class scpTool( RmsTool ):
    REMOTE_PATTERN = '^([a-zA-Z][a-zA-Z0-9_]+@[a-zA-Z][a-zA-Z0-9_]+)(:(.+))?$'
    REMOTE_GRP_USER_HOST = 1
    REMOTE_GRP_PATH = 3
    
    def getDeps( self ) :
        return [ 'ssh' ]
    
    def rmsPromote( self, config, package, rms_pool ) :
        scpBin = config['env']['scpBin']
        rms_repo = config['rmsRepo']

        package_basename = os.path.basename( package )
        dst = os.path.join( rms_repo, rms_pool, package_basename )
        
        if os.path.exists( package ) :
            self._callExternal( [ scpBin, '-Bq', package, dst ] )
        else :
            src = os.path.join( rms_repo, package )

            self._callExternal( [ scpBin, '-Bq', src, package_basename ] )
            self.rmsVerifyHash( config, package_basename )

            # Note: promotion must no re-upload an artifact to avoid
            # risk of modifications
            self._callExternal( [ scpBin, '-Bq', src, dst ] )

    def rmsGetList( self, config, rms_pool, package_hint ):
        env = config['env']
        rms_repo = config['rmsRepo']
        result = re.match( self.REMOTE_PATTERN, rms_repo )
        
        if result:
            user_host = result.group( self.REMOTE_GRP_USER_HOST )
            path = os.path.join( result.group( self.REMOTE_GRP_PATH ), rms_pool )
            cmd = 'ls {0}'.format( path )
            ret = self._callExternal( [ env['sshBin'], '-t', user_host, '--', cmd ] ).split("\n")
        else:
            path = os.path.join( rms_repo, rms_pool )  
            ret = os.listdir(path)
    
        return ret
    
    def rmsRetrieve( self, config, rms_pool, package ):
        scpBin = config['env']['scpBin']
        package_basename = os.path.basename( package )
        src = os.path.join( config['rmsRepo'], rms_pool, package_basename )
        self._callExternal( [ scpBin, '-Bq', src, package_basename ] )
    