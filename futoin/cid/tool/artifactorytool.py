#
# Copyright 2015-2019 Andrey Galkin <andrey@futoin.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from ..rmstool import RmsTool


class artifactoryTool(RmsTool):
    """JFrog Artifactory: Artifact Repository Manager.

Home: https://www.jfrog.com/artifactory/

Note 1: JFrog CLI is used for operation. So, you have all flexibility
to setup different authentication schemes:
> cte jfrog rt config --enc-password=false
or
> cte jfrog rt config --apiKey=
The first found matching URL will be used.

Alternatively, you can set env in ~/.futoin.json. Please avoid
setting env variables for security reasons.

Note 2: Artifactory OSS API is limited and may not support all commands
    (e.g. pool create). So, Artifactory Pro is assumed.

Note 3: only the part before '/' of 'rms_pool' becomes actual RMS pool
"""
    __slots__ = ()

    def getDeps(self):
        return ['jfrog']

    def envNames(self):
        return ['artifactoryUser', 'artifactoryPassword', 'artifactoryApiKey']

    def initEnv(self, env):
        self._environ['JFROG_CLI_LOG_LEVEL'] = 'ERROR'
        self._have_tool = True

    def rmsUpload(self, config, rms_pool, package_list):
        ospath = self._ospath
        self._checkFileUpload(config, rms_pool, package_list)

        server_cfg = self._getServerConfig(config)

        for package in package_list:
            self._executil.callExternal([
                config['env']['jfrogBin'],
                'rt', 'upload',
                '--server-id={0}'.format(server_cfg['serverId']),
                '--url={0}'.format(config['rmsRepo']),
                '--flat=true',
                '--recursive=false',
                '--regexp=false',
                package,
                '{0}/{1}'.format(rms_pool, ospath.basename(package))
            ])

    def rmsPromote(self, config, src_pool, dst_pool, package_list):
        self._checkFileUpload(config, dst_pool, package_list)

        server_cfg = self._getServerConfig(config)

        for package in package_list:
            self._executil.callExternal([
                config['env']['jfrogBin'],
                'rt', 'copy',
                '--server-id={0}'.format(server_cfg['serverId']),
                '--url={0}'.format(config['rmsRepo']),
                '--flat=true',
                '--recursive=false',
                '{0}/{1}'.format(src_pool, package),
                '{0}/{1}'.format(dst_pool, package)
            ])

    def rmsGetList(self, config, rms_pool, package_hint):
        ospath = self._ospath
        (pool, path) = self._prepParts(rms_pool, package_hint or '*')

        result = self._callArtifactory(
            config,
            'GET', '/api/search/pattern',
            params={
                'pattern': '{0}:{1}'.format(pool, path),
            }
        )

        result.raise_for_status()

        result = result.json()
        result = [ospath.basename(r) for r in result['files']]
        return result

    def rmsRetrieve(self, config, rms_pool, package_list):
        server_cfg = self._getServerConfig(config)

        for package in package_list:
            self._executil.callExternal([
                config['env']['jfrogBin'],
                'rt', 'download',
                '--server-id={0}'.format(server_cfg['serverId']),
                '--url={0}'.format(config['rmsRepo']),
                '--flat=true',
                '--recursive=false',
                '{0}/{1}'.format(rms_pool, package),
                package])

    def rmsPoolCreate(self, config, rms_pool):
        rms_pool = rms_pool.split('/')[0]
        check = self._callArtifactory(
            config,
            'GET', '/api/repositories/{0}'.format(rms_pool),
        )

        if check.ok:
            check = check.json()

            if check['packageType'] != 'generic':
                self._errorExit('Artifactory pool {0} already exists with different type {1}'.format(
                    rms_pool, check['packageType']))

            return

        result = self._callArtifactory(
            config,
            'PUT', '/api/repositories/{0}'.format(rms_pool),
            json={
                'rclass': 'local',
                'packageType': 'generic',
                'repoLayoutRef': 'simple-default',
            }
        )
        result.raise_for_status()

    def rmsPoolList(self, config):
        result = self._callArtifactory(
            config,
            'GET', '/api/repositories'
        )

        result.raise_for_status()

        result = result.json()
        result = [r['key'] for r in result]
        return result

    def rmsGetHash(self, config, rms_pool, package, hash_type):
        result = self._callArtifactory(
            config,
            'GET', '/api/storage/{0}/{1}'.format(rms_pool, package)
        )

        result.raise_for_status()
        result = result.json()

        if hash_type == 'sha256' and 'sha256' not in result['checksums']:
            (pool, path) = self._prepParts(rms_pool, package)

            result = self._callArtifactory(
                config,
                'POST', '/api/checksum/sha256',
                json={
                    'repoKey': pool,
                    'path': path,
                }
            )
            result.raise_for_status()

            result = self._callArtifactory(
                config,
                'GET', '/api/storage/{0}/{1}'.format(rms_pool, package)
            )

            result.raise_for_status()
            result = result.json()

        return result['checksums'][hash_type]

    def _callArtifactory(self, config, method, path, **kwargs):
        import requests

        rms_repo = config['rmsRepo']
        if rms_repo[-1] == '/':
            path = path[1:]

        url = rms_repo + path

        server_cfg = self._getServerConfig(config)

        if 'apiKey' in server_cfg:
            headers = kwargs.setdefault('headers', {})
            headers['X-JFrog-Art-Api'] = server_cfg['apiKey']
        elif 'password' in server_cfg:
            kwargs['auth'] = (server_cfg['user'], server_cfg['password'])

        self._configutil.requestsOptions(config['env'], kwargs)

        self._info('HTTP call {0} {1}'.format(method, url))
        return requests.request(method, url, **kwargs)

    def _getServerConfig(self, config, repeat=False):
        url = config['rmsRepo']

        if url[-1] != '/':
            url += '/'

        pathutil = self._pathutil
        jfrog_cfg = pathutil.safeJoin(
            self._environ['HOME'], '.jfrog', 'jfrog-cli.conf')
        jfrog_cfg = pathutil.loadJSONConfig(jfrog_cfg)

        if jfrog_cfg:
            for server_cfg in jfrog_cfg.get('artifactory', []):
                if 'serverId' in server_cfg and server_cfg.get('url', None) == url:
                    return server_cfg

        env = config['env']

        if repeat:
            pass
        elif 'artifactoryUser' in env and 'artifactoryPassword' in env:
            self._executil.callExternal([
                env['jfrogBin'],
                'rt', 'config',
                '--interactive=false',
                '--enc-password=false',
                '--url={0}'.format(url),
                '--user={0}'.format(env['artifactoryUser']),
                '--password={0}'.format(env['artifactoryPassword']),
                self._genServerId(),
            ])
            return self._getServerConfig(config, True)
        elif 'artifactoryApiKey' in env:
            self._executil.callExternal([
                env['jfrogBin'],
                'rt', 'config',
                '--interactive=false',
                '--url={0}'.format(url),
                '--apikey={0}'.format(env['artifactoryApiKey']),
                self._genServerId(),
            ])
            return self._getServerConfig(config, True)

        self._errorExit(
            'Please make sure Artifactory server is configured in JFrog CLI. See tool desc.')

    def _genServerId(self):
        rndm = self._ext.binascii.hexlify(self._os.urandom(8))
        rndm = self._executil.toString(rndm)
        return 'cid-' + rndm

    def _checkFileUpload(self, config, rms_pool, package_list):
        ospath = self._ospath

        for package in package_list:
            package = ospath.basename(package)
            res = self.rmsGetList(config, rms_pool, package)

            if res:
                self._errorExit(
                    'Package {0} already exists in RMS pool {1}'.format(package, rms_pool))

    def _prepParts(self, rms_pool, package):
        rms_pool = rms_pool.split('/', 1)

        path = ''

        if len(rms_pool) == 2:
            path += rms_pool[1] + '/'

        path += package

        return (rms_pool[0], path)
