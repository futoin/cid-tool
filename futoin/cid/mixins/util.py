
from __future__ import print_function, absolute_import

import os
import json
import stat
import shutil
import sys
import grp
import time
import tempfile
import re
from collections import OrderedDict
from ..coloring import Coloring


class UtilMixIn(object):
    _FUTOIN_JSON = 'futoin.json'

    def _updateEnvFromOutput(self, env_to_set):
        env_to_set = env_to_set.split("\n")

        for e in env_to_set:
            if not e:
                continue
            n, v = e.split('=', 1)
            os.environ[n] = v

    def autoDetectFiles(self):
        return None

    def _autoDetectByCfg(self, config, file_name):
        if self._name in config.get('toolOrder', []):
            return True

        if type(file_name) is type(''):
            file_name = [file_name]

        root_list = config['projectRootSet']

        for f in file_name:
            if f in root_list:
                return True

        return False

    #---
    def _loadJSONConfig(self, file_name, defvalue=None):
        if os.path.exists(file_name):
            with open(file_name, 'r') as content_file:
                content = content_file.read()

                def object_pairs_hook(pairs): return OrderedDict(pairs)
                return json.loads(content, object_pairs_hook=object_pairs_hook)
        else:
            return defvalue

    def _updateJSONConfig(self, file_name, updater, indent=2, separators=(',', ': ')):
        content = self._loadJSONConfig(file_name)

        if content is None:
            return []

        updater(content)

        self._writeJSONConfig(file_name, content, indent, separators)

        return [file_name]

    def _writeJSONConfig(self, file_name, content, indent=2, separators=(',', ': ')):
        with open(file_name, 'w') as content_file:
            content = json.dumps(content, indent=indent, separators=separators)
            content_file.write(content)
            content_file.write("\n")

    #---
    def _readTextFile(self, file_name):
        with open(file_name, 'r') as content_file:
            return content_file.read()

    def _updateTextFile(self, file_name, updater):
        content = self._readTextFile(file_name)
        content = updater(content)
        self._writeTextFile(file_name, content)

        return [file_name]

    def _writeTextFile(self, file_name, content):
        with open(file_name, 'w') as content_file:
            content_file.write(content)

    def _writeBinaryFile(self, file_name, content):
        try:
            content = content.encode(encoding='UTF-8')
        except:
            pass

        with open(file_name, 'wb') as content_file:
            content_file.write(content)

    def _writeIni(self, file_name, content):
        str_content = []

        for (sn, sv) in content.items():
            str_content.append('[{0}]'.format(sn))

            for (cn, cv) in sv.items():
                if isinstance(cv, list):
                    for cvi in cv:
                        str_content.append('{0} = {1}'.format(cn, cvi))
                else:
                    str_content.append('{0} = {1}'.format(cn, cv))

            str_content.append('')

        str_content = "\n".join(str_content)

        try:
            str_content = str_content.encode(encoding='UTF-8')
        except:
            pass

        with open(file_name, 'wb') as content_file:
            content_file.write(str_content)

    #---
    def _isExternalToolsSetup(self, env):
        return env['externalSetup'] != False

    def _mkDir(self, dir):
        try:
            os.mkdir(dir)
        except OSError:
            if not os.path.exists(dir):
                raise

    def _rmTree(self, dir):
        self._info(dir, 'Removing: ')

        os.chmod(dir, stat.S_IRWXU)
        for (path, dirs, files) in os.walk(dir):
            for id in dirs + files:
                id = os.path.join(path, id)
                st_mode = os.lstat(id).st_mode

                if stat.S_ISLNK(st_mode):
                    if 'lchmod' in os.__dict__:
                        # pylint: disable=no-member
                        os.lchmod(id, stat.S_IRWXU)
                else:
                    os.chmod(id, stat.S_IRWXU)

        shutil.rmtree(dir)

    def _chmodTree(self, dir, dperm, fperm, keep_execute=False):
        walk_list = os.walk(dir)
        os.chmod(dir, dperm)

        for (path, dirs, files) in walk_list:
            for f in dirs + files:
                f = os.path.join(path, f)

                st_mode = os.lstat(f).st_mode

                if stat.S_ISLNK(st_mode):
                    if 'lchmod' in os.__dict__:
                        # pylint: disable=no-member
                        os.lchmod(f, fperm)
                    continue

                if stat.S_ISDIR(st_mode):
                    os.chmod(f, dperm)
                elif keep_execute:
                    xperm = st_mode & (stat.S_IXUSR | stat.S_IXGRP)
                    os.chmod(f, fperm | xperm)
                else:
                    os.chmod(f, fperm)

    #---
    def _getTune(self, config, key, default=None):
        return config.get('toolTune', {}).get(self._name, {}).get(key, default)

    def _info(self, msg, label=None):
        if label:
            line = Coloring.infoLabel(label) + Coloring.info(msg)
        else:
            line = Coloring.info('INFO: ' + msg)

        print(line, file=sys.stderr)

    def _warn(self, msg):
        print(Coloring.warn('WARNING: ' + msg), file=sys.stderr)

    def _errorExit(self, msg):
        raise RuntimeError(msg)

    def _isAdmin(self):
        return os.geteuid() == 0

    def _haveGroup(self, grpname):
        gid = grp.getgrnam(grpname)[2]
        return gid in os.getgroups()

    def _cacheDir(self, key):
        cache_dir = os.path.join(
            os.environ['HOME'], '.cache', 'futoin-cid', key)

        try:
            os.makedirs(cache_dir)
        except:
            pass

        return cache_dir

    def _tmpCacheDir(self, **kwargs):
        tmp_dir = self._cacheDir('tmp')

        # do once a day
        base_ts = int(time.time()) - (24 * 60 * 60)
        placeholder = os.path.join(tmp_dir, 'cleanup.stamp')

        if os.path.exists(placeholder) and os.stat(placeholder).st_mtime > base_ts:
            pass
        else:
            for f in os.listdir(tmp_dir):
                fp = os.path.join(tmp_dir, f)
                s = os.stat(fp)

                if s.st_mtime <= base_ts:
                    if stat.S_ISDIR(s.st_mode):
                        self._rmTree(fp)
                    else:
                        os.remove(fp)
            self._writeTextFile(placeholder, '')

        return tempfile.mkdtemp(dir=tmp_dir, **kwargs)

    def _timeouts(self, env, fmt):
        timeouts = env['timeouts']
        connect_to = int(timeouts['connect'])
        read_to = int(timeouts['read'])
        total_to = int(timeouts['total'])

        if fmt == 'requests':
            return (connect_to, read_to)
        elif fmt == 'curl':
            return [
                '--connect-timeout', '{0}'.format(int(connect_to)),
                '--max-time', '{0}'.format(int(total_to)),
            ]

        raise NotImplementedError('Unknown format: {0}'.format(fmt))

    #---
    __memory_mult_table = {
        'B': 1,
        'K': (1 << 10),
        'M': (1 << 20),
        'G': (1 << 30),
    }

    def _parseMemory(self, val):
        b = int(val[:-1])
        m = self.__memory_mult_table[val[-1]]

        if b <= 0:
            raise ValueError('Memory must be positive')

        return b * m

    def _toMemory(self, val):
        res = None
        old_v = 0

        for (k, v) in self.__memory_mult_table.items():
            if val % v:
                continue
            elif v > old_v:
                res = '{0}{1}'.format(int(val / v), k)
                old_v = v

        return res

    #---
    def _versionSort(self, verioned_list):
        def castver(v):
            res = re.split(r'[\W_]+', v)
            for (i, vc) in enumerate(res):
                try:
                    res[i] = int(vc, 10)
                except:
                    pass
            return res

        verioned_list.sort(key=castver)

    def _getLatest(self, verioned_list):
        self._versionSort(verioned_list)
        return verioned_list[-1]
