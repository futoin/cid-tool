
import os
import re

from citool.subtool import SubTool

class scpTool( SubTool ):
    REMOTE_PATTERN = '^([a-zA-Z][a-zA-Z0-9_]+@[a-zA-Z][a-zA-Z0-9_]+)(:(.+))?$'
    REMOTE_GRP_USER_HOST = 1
    REMOTE_GRP_PATH = 3
    
    def getType( self ):
        return self.TYPE_RMS

    def getDeps( self ) :
        return [ 'ssh' ]

    def _installTool( self, env ):
        self.require_deb(['openssh-client'])
    
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

    def rmsGetLatest( self, config, rms_pool ) :
        sshBin = config['env']['sshBin']
        rms_repo = config['rmsRepo']
        result = re.match( self.REMOTE_PATTERN, rms_repo )
        cmd = 'cd {0} && ls | sort -Vr | head -n1'
        
        if result:
            user_host = result.group( self.REMOTE_GRP_USER_HOST )
            path = os.path.join( result.group( self.REMOTE_GRP_PATH ), rms_pool )
            cmd = cmd.format( path )
            ret = self._callExternal( [ sshBin, '-t', user_host, '--', cmd ] )
        else:
            path = os.path.join( rms_repo, rms_pool )  
            cmd = cmd.format( path )
            ret = self._callExternal( [ 'sh', '-c', cmd ] )
    
        return ret.strip()
    
    def rmsRetrieve( self, config, rms_pool, package ):
        scpBin = config['env']['scpBin']
        package_basename = os.path.basename( package )
        src = os.path.join( config['rmsRepo'], rms_pool, package_basename )
        self._callExternal( [ scpBin, '-Bq', src, package_basename ] )
    