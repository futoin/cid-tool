#
# Copyright 2015-2020 Andrey Galkin <andrey@futoin.org>
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


def sort(verioned_list):
    def castver(v):
        res = _ext.re.split(r'[\W_]+', v)
        for (i, vc) in enumerate(res):
            try:
                res[i] = int(vc, 10)
            except:
                pass
        return res

    verioned_list.sort(key=castver)


def latest(verioned_list):
    sort(verioned_list)
    return verioned_list[-1]
