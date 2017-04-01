
import os, glob

from ..runtimetool import RuntimeTool
from .javatoolmixin import JavaToolMixIn

class javaTool( RuntimeTool, JavaToolMixIn ):
    """Java Runtime Environment.
    
Home: http://openjdk.java.net/

Due to issues with Oracle's licensing, cid
supports only automatic installation of OpenJDK.

javaVer supports:
- only one digit like 6, 7, 8, 9 (Zulu JDK (http://zulu.org)
- use javaBin for custom JRE
"""
    def envNames( self ) :
        return ['javaBin', 'javaVer']
    
    def _installTool( self, env ):
        if 'javaVer' in env:
            ver = env['javaVer'].split('.')[0]

            if self._isFedora():
                self._requireYum(['java-1.{0}.0-openjdk'.format(ver)])
                return
            
            self._addAptRepo('zulu', 'deb http://repos.azulsystems.com/debian stable main', self._ZULU_GPG_KEY)
            self._addYumRepo('zulu', 'http://repos.azulsystems.com/rhel/zulu.repo', self._ZULU_GPG_KEY)
            self._addZypperRepo('zulu', 'http://repos.azulsystems.com/sles/latest', self._ZULU_GPG_KEY)
            
            # leaving here for possible future use
            #self._requireDeb(['openjdk-{0}-jre-headless'.format(ver)])
            #self._requireYum(['java-1.{0}.0-openjdk'.format(ver)])
            #self._requireZypper(['java-1_{0}_0-openjdk'.format(ver)])
            self._requirePackages(['zulu-{0}'.format(ver)])
            
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
        if 'javaBin' in env:
            bin_dir = os.path.dirname(env['javaBin'])
            java_home = os.path.dirname(env['javaBin'])
            
            os.environ['JAVA_HOME'] = java_home
            os.environ['JRE_HOME'] = java_home
            self._addBinPath(bin_dir, True)
            
            super(javaTool, self).initEnv( env, 'java' )
            return
        
        env.setdefault('javaVer', self._LATEST_JAVA)
        ver = env['javaVer'].split('.')[0]
        
        candidates = [
            # Zulu
            '/usr/lib/jvm/zulu-{0}*/jre/bin/java'.format(ver),
            # Debian / Ubuntu
            #"/usr/lib/jvm/java-{0}-openjdk*/jre/bin/java".format(ver),
            # RedHat
            #"/usr/lib/jvm/jre-1.{0}.0/bin/java".format(ver),
            # OpenSuse
            #"/usr/lib*/jvm/jre-1.{0}.0/bin/java".format(ver),
            # Default oracle
            #"/opt/jdk/jdk1.{0}*/bin/java".format(ver),
        ]

        if self._isGentoo() or self._isArchLinux():
            candidates += [
                "/usr/lib/jvm/java-{0}-openjdk*/jre/bin/java".format(ver),
            ]
            
        if self._isFedora():
            if int(ver) < 8:
                ver = '8'
                env['javaVer'] = ver
                
            candidates += [
                "/usr/lib/jvm/jre-1.{0}.0/bin/java".format(ver),
            ]
        
        for c in candidates:
            bin_name = glob.glob(c)
            
            if bin_name:
                bin_name = bin_name[0]
                bin_dir = os.path.dirname(bin_name)
                java_home = os.path.dirname(bin_dir)
                
                env['javaBin'] = bin_name
                os.environ['JAVA_HOME'] = java_home
                os.environ['JRE_HOME'] = java_home
                self._addBinPath(bin_dir, True)
                self._have_tool = True
                break
                
    def onRun( self, config, file, args, tune ):
        env = config['env']
        self._callInteractive([
            env[self._name + 'Bin'], '-jar', file
        ] + args)
            
    _ZULU_GPG_KEY = '''
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1

mQINBFNgFa8BEADTL/REB10M+TfiZOtFHqL5LHKkzTMn/O2r5iIqXGhi6iwZazFs
9S5g1eU7WMen5Xp9AREs+OvaHx91onPZ7ZiP7VpZ6ZdwWrnVk1Y/HfI59tWxmNYW
DmKYBGMj4EUpFPSE9EnFj7dm1WdlCvpognCwZQl9D3BseGqN7OLHfwqqmOlbYN9h
HYkT+CaqOoWDIGMB3UkBlMr0GuujEP8N1gxg7EOcSCsZH5aKtXubdUlVSphfAAwD
z4MviB39J22sPBnKmaOT3TUTO5vGeKtC9BAvtgA82jY2TtCEjetnfK/qtzj/6j2N
xVUbHQydwNQVRU92A7334YvCbn3xUUNI0WOscdmfpgCU0Z9Gb2IqDb9cMjgUi8F6
MG/QY9/CZjX62XrHRPm3aXsCJOVh/PO1sl2A/rvv8AkpJKYyhm6T8OBFptCsA3V4
Oic7ZyYhqV0u2r4NON+1MoUeuuoeY2tIrbRxe3ffVOxPzrESzSbc8LC2tYaP+wGd
W0f57/CoDkUzlvpReCUI1Bv5zP4/jhC63Rh6lffvSf2tQLwOsf5ivPhUtwUfOQjg
v9P8Wc8K7XZpSOMnDZuDe9wuvB/DiH/P5yiTs2RGsbDdRh5iPfwbtf2+IX6h2lNZ
XiDKt9Gc26uzeJRx/c7+sLunxq6DLIYvrsEipVI9frHIHV6fFTmqMJY6SwARAQAB
tEdBenVsIFN5c3RlbXMsIEluYy4gKFBhY2thZ2Ugc2lnbmluZyBrZXkuKSA8cGtp
LXNpZ25pbmdAYXp1bHN5c3RlbXMuY29tPokCOAQTAQIAIgUCU2AVrwIbAwYLCQgH
AwIGFQgCCQoLBBYCAwECHgECF4AACgkQsZmDYSGb2cnJ8xAAz1V1PJnfOyaRIP2N
Ho2uRwGdPsA4eFMXb4Z08eGjDMD3b9WW3D0XnCLbJpaZ6klz0W0s2tcYSneTBaSs
RAqxgJgBZ5ZMXtrrHld/5qFoBbStLZLefmcPhnfvamwHDCTLUex8NIAI1u3e9Rhb
5fbH+gpuYpwHX7hz0FOfpn1sxR03UyxU+ey4AdKe9LG3TJVnB0WcgxpobpbqweLH
yzcEQCNoFV3r1rlE13Y0aE31/9apoEwiYvqAzEmE38TukDLl/Qg8rkR1t0/lok2P
G6pWqdN7pmoUovBTvDi5YOthcjZcdOTXXn2Yw4RZVF9uhRsVfku1Eg25SnOje3uY
smtQLME4eESbePdjyV/okCIle66uHZse+7gNyNmWpf01hM+VmAySIAyKa0Ku8AXZ
MydEcJTebrNfW9uMLsBx3Ts7z/CBfRng6F8louJGlZtlSwddTkZVcb26T20xeo0a
ZvdFXM2djTi/a5nbBoZQL85AEeV7HaphFLdPrgmMtS8sSZUEVvdaxp7WJsVuF9cO
Nxsvx40OYTvfco0W41Lm8/sEuQ7YueEVpZxiv5kX56GTU9vXaOOi+8Z7Ee2w6Adz
4hrGZkzztggs4tM9geNYnd0XCdZ/ICAskKJABg7biDD1PhEBrqCIqSE3U497vibQ
Mpkkl/Zpp0BirhGWNyTg8K4JrsQ=
=d320
-----END PGP PUBLIC KEY BLOCK-----
'''
            
