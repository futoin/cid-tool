
import os
import re
import shutil

from ..rmstool import RmsTool


class archivaTool(RmsTool):
    """Apache Archiva: The Build Artifact Repository Manager.
Home: https://archiva.apache.org/

NOT IMPLEMENTED YET!
"""

    def envNames(self):
        return ['archivaUser', 'archivaPassword']

    def initEnv(self, env):
        self._have_tool = True

    def rmsUpload(self, config, rms_pool, package_list):
        for package in package_list:
            package_basename = os.path.basename(package)
            path = '/repository/{0}/{1}'.format(rms_pool, package_basename)

            res = self._callArchiva(config, 'HEAD', path)

            if res.ok:
                self._errorExit(
                    'Package {0} already exists on RMS'.format(package_basename))

            hashes = self.rmsCalcHashes(package)

            with open(package, 'rb') as pf:
                res = self._callArchiva(
                    config,
                    'PUT', path,
                    data=pf
                )

                res.raise_for_status()

                for (hash_type, hash_value) in hashes.items():
                    res = self._callArchiva(
                        config,
                        'PUT', '{0}.{1}'.format(path, hash_type),
                        data='{0}  {1}'.format(hash_value, package_basename),
                    )
                    res.raise_for_status()

    def rmsPromote(self, config, src_pool, dst_pool, package_list):
        for package in package_list:
            src_path = '/repository/{0}/{1}'.format(src_pool, package)
            dst_path = '/repository/{0}/{1}'.format(dst_pool, package)

            res = self._callArchiva(
                config,
                'COPY', src_path,
                headers={
                    'Depth': '0',
                    'Overwrite': 'F',
                    'Destination': dst_path,
                }
            )
            res.raise_for_status()

            for hash_type in self.ALLOWED_HASH_TYPES:
                src_hash = '{0}.{1}'.format(src_path, hash_type)

                res = self._callArchiva(config, 'GET', src_hash)

                if res.status_code == 404:
                    continue

                res.raise_for_status()

                res = self._callArchiva(
                    config,
                    'PUT', '{0}.{1}'.format(dst_path, hash_type),
                    data=res.text
                )
                res.raise_for_status()

    def rmsGetList(self, config, rms_pool, package_hint):
        apires = self._callArchiva(
            config,
            'PROPFIND', '/repository/{0}/'.format(rms_pool),
            headers={
                'Depth': '1',
                'Content-type': 'text/xml; charset="utf-8"'
            },
            data='''<?xml version="1.0" encoding="utf-8" ?>
<propfind xmlns="DAV:">
  <prop>
    <displayname/>
    <iscollection/>
  </prop>
</propfind>'''
        )
        apires.raise_for_status()

        import xml.dom.minidom as minidom
        try:
            apidom = minidom.parseString(apires.text)
        except:
            self._warn(apires.text)
            raise

        ret = []

        for response in apidom.getElementsByTagNameNS('*', 'response'):
            if response.getElementsByTagNameNS('*', 'iscollection')[0].firstChild.nodeValue == '0':
                name = response.getElementsByTagNameNS(
                    '*', 'displayname')[0].firstChild.nodeValue
                (sname, sext) = os.path.splitext(name)

                if sext and sext[1:] in self.ALLOWED_HASH_TYPES:
                    continue

                ret.append(name)

        return ret

    def rmsRetrieve(self, config, rms_pool, package_list):
        for package in package_list:
            result = self._callArchiva(
                config,
                'GET',
                '/repository/{0}/{1}'.format(rms_pool, package),
                stream=True
            )
            result.raise_for_status()

            with open(package, 'wb') as f:
                result.raw.decode_content = True
                shutil.copyfileobj(result.raw, f)

    def rmsPoolCreate(self, config, rms_pool):
        res = self._callArchiva(
            config,
            'GET', '/restServices/archivaServices/managedRepositoriesService/getManagedRepository/{0}'.format(
                rms_pool),
            headers={'Accept': 'application/json'},
        )

        if res.ok and len(res.text) and res.json()['id'] == rms_pool:
            return

        res = self._callArchiva(
            config,
            'POST', '/restServices/archivaServices/managedRepositoriesService/addManagedRepository',
            headers={'Accept': 'application/json'},
            json={
                'id': rms_pool,
                'name': rms_pool,
                'blockRedeployments': True,
                'cronExpression': "0 0 * * * ?",
                'indexDirectory': '.indexer',
                'layout': "default",
                'location': rms_pool,
                'releases': True,
                'scanned': False,  # produces issue with Lucene locks
                'skipPackedIndexCreation': True,
                'snapshots': False,
            }
        )

        if not res.ok:
            self._warn(res.text)
        res.raise_for_status()
        assert res.json()['id'] == rms_pool

    def rmsPoolList(self, config):
        res = self._callArchiva(
            config,
            'GET', '/restServices/archivaServices/managedRepositoriesService/getManagedRepositories',
            headers={'Accept': 'application/json'},
        )
        res.raise_for_status()
        res = res.json()

        return [r['id'] for r in res]

    def rmsGetHash(self, config, rms_pool, package, hash_type):
        path = '{0}/{1}.{2}'.format(rms_pool, package, hash_type)

        res = self._callArchiva(
            config,
            'GET', '/repository/{0}/{1}.{2}'.format(
                rms_pool, package, hash_type)
        )
        res.raise_for_status()
        return res.text.split()[0].strip()

    def _callArchiva(self, config, method, path, **kwargs):
        env = config['env']

        rms_repo = config['rmsRepo']
        if rms_repo[-1] == '/':
            path = path[1:]

        url = rms_repo + path

        if 'archivaUser' in env and 'archivaPassword' in env:
            kwargs['auth'] = (env['archivaUser'], env['archivaPassword'])

        kwargs['timeout'] = self._timeouts(env, 'requests')

        self._info('HTTP call {0} {1}'.format(method, url))
        import requests
        return requests.request(method, url, **kwargs)
