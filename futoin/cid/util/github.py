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

from ..mixins.ondemand import ext as _ext
from . import log as _log

_api_url = 'https://api.github.com'
_api_ver = 'application/vnd.github.v3+json'


def api_call(env, method, path, **kwargs):
    url = _api_url + path
    _ext.configutil.requestsOptions(env, kwargs)

    headers = kwargs.setdefault('headers', {})
    headers.setdefault('Accept', _api_ver)

    return _ext.requests.request(method, url, **kwargs)


def listReleases(env, repo):
    res = api_call(env, 'GET',
                   '/repos/{0}/releases'.format(repo))
    res.raise_for_status()
    return res.json()


def releaseInfo(env, repo, ver):
    res = api_call(env, 'GET',
                   '/repos/{0}/releases/{1}'.format(repo, ver))
    res.raise_for_status()
    return res.json()


def findAsset(assets, content_type):
    for asset in assets:
        if asset['content_type'] == content_type:
            return asset
    else:
        _log.errorExit('Failed to find .tar.gz asset')
