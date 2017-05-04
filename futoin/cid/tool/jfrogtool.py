
import os, stat

from ..runenvtool import RunEnvTool

class jfrogTool( RunEnvTool ):
    """JFrog: Command Line Interface for Artifactory and Bintray

Home: https://www.jfrog.com/confluence/display/CLI/JFrog+CLI
"""
    def _installTool( self, env ):
        dst_dir = env['jfrogDir']
        curl_bin = env['curlBin']
        get_url = env['jfrogGet']
        jfrog_bin = env['jfrogBin']
        
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        
        if self._isMacOS() :
            self._requireHomebrew('jfrog-cli-go')
        else:
            self._callExternal([curl_bin, '-fsSL', get_url, '-o', jfrog_bin])
            os.chmod(jfrog_bin, stat.S_IRWXU|stat.S_IRGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IXOTH)

    def updateTool( self, env ):
        self.uninstallTool( env )
        self._installTool( env )

    def uninstallTool( self, env ):
        jfrog_bin = env['jfrogBin']
        if os.path.exists(jfrog_bin):
            os.remove(jfrog_bin)
        self._have_tool = False
        
    def envNames( self ) :
        return [ 'jfrogDir', 'jfrogBin', 'jfrogGet' ]

    def initEnv( self, env ) :
        bin_dir = env.setdefault('jfrogDir', env['binDir'])
        jfrog_bin = env.setdefault('jfrogBin', os.path.join(bin_dir, 'jfrog'))
        
        pkg = None
        url_base = 'https://api.bintray.com/content/jfrog/jfrog-cli-go/$latest'
        
        if self._isMacOS() :
            pass
        elif self._isAMD64():
            pkg = 'jfrog-cli-linux-amd64'
        else:
            pkg = 'jfrog-cli-linux-386'
            
        if pkg:
            env.setdefault(
                'jfrogGet',
                'https://api.bintray.com/content/jfrog/jfrog-cli-go/$latest/{0}/jfrog?bt_package={0}'.format(pkg)
            )
            

        self._addBinPath( bin_dir )

        self._have_tool = os.path.exists( jfrog_bin )
    
    def getDeps( self ) :
        return ['curl' ]
