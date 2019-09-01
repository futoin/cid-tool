#
# Copyright 2019 Andrey Galkin <andrey@futoin.org>
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
from .piptoolmixin import PipToolMixIn


class awsTool(PipToolMixIn, RmsTool):
    """Generic AWS CLI and S3 as RMS.

Home: https://docs.aws.amazon.com/cli/index.html
"""
    __slots__ = ()

    def getDeps(self):
        return ['pip']

    def _pipName(self):
        return 'awscli'

    def rmsUpload(self, config, rms_pool, package_list):
        ospath = self._ospath
        bucket, path = self._getS3Repo(config)

        for package in package_list:
            package_basename = ospath.basename(package)
            self.onExec(config['env'], [
                's3', 'cp', package,
                's3://{0}{1}/{2}/{3}'.format(bucket,
                                             path, rms_pool, package_basename),
            ], False)

    def rmsPromote(self, config, src_pool, dst_pool, package_list):
        ospath = self._ospath
        bucket, path = self._getS3Repo(config)

        for package in package_list:
            package_basename = ospath.basename(package)
            self.onExec(config['env'], [
                's3', 'cp',
                's3://{0}{1}/{2}/{3}'.format(bucket,
                                             path, src_pool, package_basename),
                's3://{0}{1}/{2}/{3}'.format(bucket,
                                             path, dst_pool, package_basename),
            ], False)

    def rmsGetList(self, config, rms_pool, package_hint):
        bucket, path = self._getS3Repo(config)

        res = self._executil.callExternal([
            config['env']['awsBin'],
            's3', 'ls',
            's3://{0}{1}/{2}/'.format(bucket, path, rms_pool)])
        return [r.split()[-1] for r in res.rstrip().split('\n')]

    def rmsRetrieve(self, config, rms_pool, package_list):
        bucket, path = self._getS3Repo(config)

        for package in package_list:
            self.onExec(config['env'], [
                's3', 'cp',
                's3://{0}{1}/{2}/{3}'.format(bucket, path, rms_pool, package),
                package,
            ], False)

    def rmsGetHash(self, config, rms_pool, package, hash_type):
        # Note: Etag is not always MD5, so we skip
        raise NotImplementedError(self._name)

    def rmsPoolCreate(self, config, rms_pool):
        pass

    def rmsPoolList(self, config):
        return self.rmsGetList(config, '', '')

    def _getS3Repo(self, config):
        rms_repo = config['rmsRepo']
        parsed = self._ext.urlparse.urlparse(rms_repo)

        if parsed.scheme != 's3':
            self._errorExit(
                'AWS S3 repository scheme must be s3://bucket/path')

        bucket = parsed.netloc
        path = parsed.path

        if len(path) > 1:
            path = path.rstrip('/')
        else:
            path = ''

        return bucket, path
