
import os
import glob

from ..runtimetool import RuntimeTool


class phpfpmTool(RuntimeTool):
    """PHP is a popular general-purpose scripting language that is especially suited to web development.

Home: http://php.net/

This tool provides PHP-FPM based website entry point support.
It means any PHP file in project can be executed with all consequences.
"""

    def getDeps(self):
        return ['php']

    def tuneDefaults(self):
        return {
            'minMemory': '1M',
            'connMemory': '8M',
            'debugConnOverhead': '24M',
            'socketTypes': ['unix', 'tcp'],
            'socketType': 'unix',
            'scalable': True,
            'maxInstances': 2,
        }

    def _installTool(self, env):
        php_ver = env['phpVer']

        if php_ver == self.SYSTEM_VER:
            self._systemDeps()
            return

        if env['phpBinOnly']:
            self._installBinaries(env)
            return

    def _installBinaries(self, env):
        ver = env['phpVer']

        if self._isDebian() or self._isUbuntu():
            self._requireDeb('php{0}-fpm'.format(ver))

        elif self._isSCLSupported():
            pass

        else:
            self._systemDeps()

    def _systemDeps(self):
        self._requireDeb(['php.*-fpm'])
        self._requireZypper(['php*-fpm'])
        self._requireYum(['php-fpm'])

    def initEnv(self, env):
        php_bin = env['phpBin']

        if env['phpVer'] == self.SYSTEM_VER:
            pass
        elif env['phpBinOnly']:
            if self._isDebian() or self._isUbuntu():
                bin_name = 'php-fpm' + env['phpVer']

            elif self._isSCLSupported():
                bin_name = 'php-fpm'

        else:
            bin_name = '{0}-fpm'.format(os.path.basename(php_bin))

        phpfpm_bin = self._which(bin_name)

        if phpfpm_bin:
            env['phpfpmBin'] = phpfpm_bin
            self._have_tool = True
            return

        #--
        phpfpm_bin = os.path.realpath(
            os.path.join(php_bin, '..', '..', 'sbin',
                         '{0}*'.format(bin_name))
        )
        phpfpm_bin = glob.glob(phpfpm_bin)

        if phpfpm_bin:
            env['phpfpmBin'] = phpfpm_bin[0]
            self._have_tool = True
            return
