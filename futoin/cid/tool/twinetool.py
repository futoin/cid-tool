
from ..rmstool import RmsTool
from .piptoolmixin import PipToolMixIn


class twineTool(PipToolMixIn, RmsTool):
    """Collection of utilities for interacting with PyPI
Home: https://pypi.python.org/pypi/twine

Not a fully supported RMS. Supports only uploading of local packages.

Note: rmsRepo is ignored and rmsPool is actual repo URL or uses ~/.pypirc entry
"""

    def getDeps(self):
        return super(twineTool, self).getDeps() + ['gpg']

    def envNames(self):
        return [
            'twineBin',
            'twineIdentity',
            'twineUser',
            'twinePassword',
        ]

    def rmsUpload(self, config, rms_pool, package_list):
        env = config['env']

        identity = env.get('twineIdentity', None)
        user = env.get('twineUser', None)
        passwd = env.get('twinePassword', None)

        cmd = [env['twineBin'], 'upload']
        cmd += ['--repository', rms_pool]

        if identity:
            cmd += ['--sign', '--identity', identity]
        elif self._getTune(config, 'requireSign', True):
            self._errorExit(
                'Twine config requires GPG signature. Please set "twineIdentity"')

        if user:
            cmd += ['--username', user]

        if passwd:
            cmd += ['--password', passwd]

        cmd.append('--skip-existing')

        cmd += package_list

        self._callInteractive(cmd, replace=False)

    def rmsPoolList(self, config):
        return [
            'pypi',
            'pypitest',
        ]
