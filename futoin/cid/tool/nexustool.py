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


class nexusTool(RmsTool):
    """Sonatype Nexus RMS.
Home: http://www.sonatype.org/nexus/

Sonatype Nexus v2 (!). Please see nexus3 tools for v3 support.

Please set user and password in ~/.futoin.json env. Please
avoid setting these variables in process environment.
"""
    __slots__ = ()

    def envNames(self):
        return ['nexusUser', 'nexusPassword']

    def initEnv(self, env):
        self._have_tool = True

    def rmsUpload(self, config, rms_pool, package_list):
        ospath = self._ospath

        for package in package_list:
            package_basename = ospath.basename(package)
            path = '/content/repositories/{0}/{1}'.format(
                rms_pool, package_basename)

            if self._callNexus(config, 'HEAD', path).ok:
                self._errorExit(
                    'Package {0} already exists on RMS'.format(package_basename))

            with open(package, 'rb') as pf:
                res = self._callNexus(
                    config,
                    'PUT', path,
                    data=pf
                )
                res.raise_for_status()

    def rmsPromote(self, config, src_pool, dst_pool, package_list):
        # TODO: find out how to copy on server
        tmpdir = self._pathutil.tmpCacheDir(prefix='nexus')
        os = self._os

        try:
            cwd = os.getcwd()
            os.chdir(tmpdir)
            self.rmsRetrieve(config, src_pool, package_list)
            self.rmsUpload(config, dst_pool, package_list)
            os.chdir(cwd)
        finally:
            self._pathutil.rmTree(tmpdir)

    def rmsGetList(self, config, rms_pool, package_hint):
        rms_pool = rms_pool.split('/', 1)
        pool = rms_pool[0]
        path = rms_pool[1] if len(rms_pool) == 2 else ''

        res = self._callNexus(
            config,
            'GET', '/service/local/repositories/{0}/content/{1}'.format(
                pool, path),
            headers={'Accept': 'application/json'},
        )
        res.raise_for_status()
        res = res.json()

        res = [r['leaf'] and r['text'] or None for r in res['data']]
        res = list(filter(None, res))
        return res

    def rmsRetrieve(self, config, rms_pool, package_list):
        shutil = self._ext.shutil

        for package in package_list:
            result = self._callNexus(
                config,
                'GET',
                '/content/repositories/{0}/{1}'.format(rms_pool, package),
                stream=True
            )
            result.raise_for_status()

            with open(package, 'wb') as f:
                result.raw.decode_content = True
                shutil.copyfileobj(result.raw, f)

    def rmsPoolCreate(self, config, rms_pool):
        res = self._callNexus(
            config,
            'GET', '/service/local/repositories/{0}'.format(rms_pool),
        )

        if res.ok:
            return

        res = self._callNexus(
            config,
            'POST', '/service/local/repositories',
            json={
                'data': {
                    'id': rms_pool,
                    'name': rms_pool,
                    'provider': 'site',
                    'format': 'site',
                    'repoType': 'hosted',
                    'exposed': True,
                    'writePolicy': 'ALLOW_WRITE_ONCE',
                    'browseable': True,
                    "repoPolicy": "MIXED",
                    "providerRole": "org.sonatype.nexus.proxy.repository.WebSiteRepository",
                }
            }
        )
        res.raise_for_status()

    def rmsPoolList(self, config):
        res = self._callNexus(
            config,
            'GET', '/service/local/all_repositories',
            headers={'Accept': 'application/json'},
        )
        res.raise_for_status()
        res = res.json()

        # case with no repos
        if 'data' not in res:
            return []

        return [r['id'] for r in res['data']]

    def rmsGetHash(self, config, rms_pool, package, hash_type):
        path = '{0}/{1}'.format(rms_pool, package)
        pool, path = path.split('/', 1)

        res = self._callNexus(
            config,
            'GET', '/service/local/repositories/{0}/content/{1}?describe=info'.format(
                pool, path),
            headers={'Accept': 'application/json'},
        )
        res.raise_for_status()
        res = res.json()

        return res['data'][hash_type + 'Hash']

    def _callNexus(self, config, method, path, **kwargs):
        env = config['env']

        rms_repo = config['rmsRepo']
        if rms_repo[-1] == '/':
            path = path[1:]

        url = rms_repo + path

        if 'nexusUser' in env and 'nexusPassword' in env:
            kwargs['auth'] = (env['nexusUser'], env['nexusPassword'])

        self._configutil.requestsOptions(env, kwargs)

        self._info('HTTP call {0} {1}'.format(method, url))
        return self._ext.requests.request(method, url, **kwargs)
