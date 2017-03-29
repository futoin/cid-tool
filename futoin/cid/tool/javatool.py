
import os, glob

from ..runtimetool import RuntimeTool

class javaTool( RuntimeTool ):
    """Java Runtime Environment.
    
Home: http://openjdk.java.net/

Due to issues with Oracle's licensing, cid
supports only automatic installation of OpenJDK.

javaVer supports only one digits like 7, 8, 9.
"""
    def envNames( self ) :
        return ['javaBin', 'javaVer']
    
    def _installTool( self, env ):
        if 'javaVer' in env:
            ver = env['javaVer'][0]
            self._requireDeb(['openjdk-{0}-jre-headless'.format(ver)])
            self._requireYum(['java-1.{0}.0-openjdk'.format(ver)])
            self._requireZypper(['java-1_{0}_0-openjdk'.format(ver)])
            self._requirePacman(['jre{0}-openjdk'.format(ver)])
            self._requireEmerge(['=dev-java/oracle-jre-bin-1.{0}*'.format(ver)])
        else :
            self._requireDeb(['default-jre-headless'])
            self._requireYum(['java-1.8.0-openjdk'])
            self._requireZypper(['java-1_8_0-openjdk'])
            self._requirePacman(['jre8-openjdk'])
            self._requireEmerge(['virtual/jre'])
    
    def uninstallTool( self, env ):
        pass

    def initEnv( self, env ) :
        if 'javaBin' in env or 'javaVer' not in env:
            super(javaTool, self).initEnv( env, 'java' )
            return
        
        ver = env['javaVer'][0]
        
        candidates = [
            # Debian / Ubuntu
            "/usr/lib/jvm/java-{0}-openjdk*/jre/bin/java".format(ver),
            # RedHat
            "/usr/lib/jvm/jre-1.{0}.0/bin/java".format(ver),
            # OpenSuse
            "/usr/lib*/jvm/jre-1.{0}.0/bin/java".format(ver),
            # Default oracle
            "/opt/jdk/jdk1.{0}*/bin/java".format(ver),
        ]
        
        for c in candidates:
            bin_name = glob.glob(c)
            
            if bin_name:
                env['javaBin'] = bin_name[0]
                self._addBinPath(os.path.basename(env['javaBin']), True)
                self._have_tool = True
                break
            
