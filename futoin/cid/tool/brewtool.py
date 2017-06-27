
import os

from ..runenvtool import RunEnvTool


class brewTool(RunEnvTool):
    """Homebrew. The missing package manager for macOS.

Home: https://brew.sh/

homebrewInstall is use for admin user installation.
brewDir & brewGit is used for local install.
"""
    _MACOS_ADMIN_GID = 80 # dirty hack for now

    def envNames(self):
        return ['brewBin', 'brewDir', 'brewGit', 'homebrewInstall']
    
    def _installTool(self, env):
        if self._isLocalBrew(env):
            homebrew_git = env['brewGit']
            homebrew_dir = env['brewDir']
            
            git = self._which('git')
        
            if not git:
                xcode_select = self._which('xcode-select')
                self._callExternal([xcode_select, '--install'])
                git = self._which('git')

            self._callExternal([git, 'clone', homebrew_git, homebrew_dir])
        else:
            # should be system-available
            curl = self._which('curl')
            ruby = self._which('ruby')
            homebrew_install = env['homebrewInstall']
            
            curl_args = self._timeouts(env, 'curl')

            brew_installer = self._callExternal(
                [ curl, '-fsSL', homebrew_install] + curl_args
            )

            self._callExternal([ruby, '-'], input=brew_installer)
    
    def _isLocalBrew(self, env):
        return env.get('brewDir', '') or self._MACOS_ADMIN_GID not in os.getgroups()

    def initEnv(self, env, bin_name=None):
        if self._isLocalBrew(env):
            homebrew_dir = os.path.join(self._deployHome(), '.homebrew')
            homebrew_dir = env.setdefault('brewDir', homebrew_dir)
            env.setdefault('brewGit',
                           'https://github.com/Homebrew/brew.git')
            
            bin_dir = os.path.join(homebrew_dir, 'bin')
            brew = os.path.join(bin_dir, 'brew')
            
            if os.path.exists(brew):
                self._addBinPath(bin_dir, True)
                env['brewBin'] = brew
                self._have_tool = True
        else:
            env.setdefault('homebrewInstall',
                           'https://raw.githubusercontent.com/Homebrew/install/master/install')
            super(brewTool, self).initEnv(env, bin_name)