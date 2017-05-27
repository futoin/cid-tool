
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
            'socketType': 'unix',
            'scalable': True,
            'maxInstances': 2,
        }

    def initEnv(self, env):
        if env['phpVer'] == self.SYSTEM_VER:
            pass
        elif env['phpBinOnly']:
            pass
        else:
            pass

        php_bin = env['phpBin']
        bin_name = os.path.basename(php_bin)

        phpfpm_bin = self._which(bin_name)

        if phpfpm_bin:
            env['phpfpmBin'] = phpfpm_bin
            self._have_tool = True
            return

        #--
        phpfpm_bin = os.path.realpath(
            os.path.join(php_bin, '..', '..', 'sbin',
                         '{0}-fpm*'.format(bin_name))
        )
        phpfpm_bin = glob.glob(phpfpm_bin)

        if phpfpm_bin:
            env['phpfpmBin'] = phpfpm_bin[0]
            self._have_tool = True
            return
