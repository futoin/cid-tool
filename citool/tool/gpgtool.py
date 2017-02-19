
from citool.subtool import SubTool

class gpgTool( SubTool ):
    def getType( self ):
        return self.TYPE_RUNENV
    
    def initEnv( self, env ):
        SubTool.initEnv( self, env )
        env.setdefault('gpgKeyServer', 'hkp://keyserver.ubuntu.com:80')
        