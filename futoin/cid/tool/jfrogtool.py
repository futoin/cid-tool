
import os
import stat

from ..runenvtool import RunEnvTool
from .curltoolmixin import CurlToolMixIn


class jfrogTool(CurlToolMixIn, RunEnvTool):
    """JFrog: Command Line Interface for Artifactory and Bintray

Home: https://www.jfrog.com/confluence/display/CLI/JFrog+CLI
"""

    def _installTool(self, env):
        if self._isMacOS():
            self._requireBrew('jfrog-cli-go')
            return

        dst_dir = env['jfrogDir']
        get_url = env['jfrogGet']
        jfrog_bin = os.path.join(dst_dir, 'jfrog')

        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        self._callCurl(env, [get_url, '-o', jfrog_bin])
        os.chmod(jfrog_bin, stat.S_IRWXU | stat.S_IRGRP |
                 stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

    def updateTool(self, env):
        if self._isMacOS():
            return

        self.uninstallTool(env)
        self._installTool(env)

    def uninstallTool(self, env):
        if self._isMacOS():
            return

        jfrog_bin = env['jfrogBin']
        if os.path.exists(jfrog_bin):
            os.remove(jfrog_bin)
        self._have_tool = False

    def envNames(self):
        return ['jfrogDir', 'jfrogBin', 'jfrogGet']

    def initEnv(self, env):
        bin_dir = env.setdefault('jfrogDir', env['binDir'])

        pkg = None
        url_base = 'https://api.bintray.com/content/jfrog/jfrog-cli-go/$latest'

        if self._isMacOS():
            pass
        elif self._isAMD64():
            pkg = 'jfrog-cli-linux-amd64'
        else:
            pkg = 'jfrog-cli-linux-386'

        if pkg:
            env.setdefault(
                'jfrogGet',
                'https://api.bintray.com/content/jfrog/jfrog-cli-go/$latest/{0}/jfrog?bt_package={0}'.format(
                    pkg)
            )

        self._addBinPath(bin_dir)

        super(jfrogTool, self).initEnv(env)

        if self._have_tool:
            env['jfrogDir'] = os.path.dirname(env['jfrogBin'])
