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


class nexus3Tool(RmsTool):
    """Sonatype Nexus RMS.
Home: http://www.sonatype.org/nexus/

PLEASE DO NOT USE. INCOMPLETE.

Nexus 3 does not support REST API yet.
So, this tool is not usable yet.

Please set user and password in ~/.futoin.json env. Please
avoid setting these variables in process environment.
"""
    __slots__ = ()

    def envNames(self):
        return ['nexus3User', 'nexus3Password']

    def initEnv(self, env):
        self._have_tool = True

    def rmsUpload(self, config, rms_pool, package_list):
        ospath = self._ospath

        for package in package_list:
            package_basename = ospath.basename(package)

            with open(package, 'rb') as pf:
                self._callNexus(
                    config,
                    'PUT',
                    '/repository/{0}/{1}'.format(rms_pool, package_basename),
                    data=pf
                )

    def rmsPromote(self, config, src_pool, dst_pool, package_list):
        # TODO: use Groovy API to transfer on server
        self.rmsRetrieve(config, src_pool, package_list)
        self.rmsUpload(config, dst_pool, package_list)

    def rmsGetList(self, config, rms_pool, package_hint):
        """script_name = 'cid_list'.format(
            rms_pool.replace('/', '$'),
            package_hint.replace('?', '$$').replace('*', '$$$')
        )

        script = [
            'return groovy.json.JsonOutput.toJson(',
        ]

        self._execNexusScript(config, script_name, script)
        """
        raise NotImplementedError(self._name)

    def rmsRetrieve(self, config, rms_pool, package_list):
        for package in package_list:
            result = self._callNexus(
                config,
                'GET',
                '/repository/{0}/{1}'.format(rms_pool, package),
                stream=True
            )
            result.raise_for_status()

            with open(package, 'wb') as f:
                result.raw.decode_content = True
                self._ext.shutil.copyfileobj(result.raw, f)

    def rmsPoolCreate(self, config, rms_pool):
        pool = rms_pool.split('/', 1)[0]

        script_name = 'cid_pool_create'

        script = [
            'import groovy.json.JsonSlurper'
            'def pool = new JsonSlurper().parseText(args)'
            "def rawStore = blobStore.createFileBlobStore(pool.name, pool.path)",
            "repository.createRawHosted(pool.name, rawStore.name)",
        ]

        self._execNexusScript(config, script_name, script, json={
            'name': pool,
            'path': pool,
        })

    def rmsPoolList(self, config):
        raise NotImplementedError(self._name)

    def rmsGetHash(self, config, rms_pool, package, hash_type):
        raise NotImplementedError(self._name)

    def _execNexusScript(self, config, script_name, script, **kwargs):
        result = self._callNexus(
            config,
            'PUT',
            '/service/siesta/rest/v1/script',
            json={
                'name': script_name,
                'type': 'groovy',
                'content': "\n".join(script),
            }
        )

        result.raise_for_status()

        result = self._callNexus(
            config,
            'POST',
            '/service/siesta/rest/v1/script/{0}/run'.format(script_name),
            **kwargs
        )

        result.raise_for_status()

        return result

    def _callNexus(self, config, method, path, **kwargs):
        env = config['env']

        rms_repo = config['rmsRepo']
        if rms_repo[-1] == '/':
            path = path[1:]

        url = rms_repo + path

        if 'nexus3User' in env and 'nexus3Password' in env:
            kwargs['auth'] = (env['nexus3User'], env['nexus3Password'])

        self._configutil.requestsOptions(env, kwargs)

        self._info('HTTP call {0} {1}'.format(method, url))
        return self._ext.requests.request(method, url, **kwargs)
