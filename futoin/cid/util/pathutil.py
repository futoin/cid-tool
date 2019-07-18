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
from . import complex_memo as _complex_memo


def which(program):
    return cachedWhich(program, _ext.os.environ["PATH"])


@_complex_memo
def cachedWhich(program, env_path):
    "Copied from stackoverflow"

    os = _ext.os
    ospath = _ext.ospath

    def is_exe(fpath):
        return ospath.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = ospath.split(program)

    if fpath:
        if is_exe(program):
            return program
    else:
        for path in env_path.split(os.pathsep):
            path = path.strip('"')
            exe_file = safeJoin(path, program)

            if is_exe(exe_file):
                return exe_file

    return None


def safeJoin(*args):
    ospath = _ext.ospath
    paths = list(args[:1]) + [p.lstrip(ospath.sep) or '.' for p in args[1:]]
    return ospath.join(*paths)


def addEnvPath(env_name, add_dir, first=False):
    os = _ext.os
    environ = os.environ

    if env_name in os.environ:
        dir_list = os.environ[env_name].split(os.pathsep)
    else:
        dir_list = []

    if add_dir not in dir_list:
        if first:
            dir_list[0:0] = [add_dir]
        else:
            dir_list.append(add_dir)

        os.environ[env_name] = os.pathsep.join(dir_list)


def delEnvPath(env_name, del_dir, fail=False):
    os = _ext.os
    environ = os.environ

    if env_name in environ:
        dir_list = environ[env_name].split(os.pathsep)

        try:
            del dir_list[dir_list.index(del_dir)]
        except ValueError:
            if fail:
                raise
    elif fail:
        # trigger KeyError
        return environ[env_name]


def addBinPath(bin_dir, first=False):
    addEnvPath('PATH', bin_dir, first=first)


def addPackageFiles(config, pattern):
    files = _ext.glob.glob(pattern)

    if not files:
        _log.errorExit(
            'Failed to find created packages of "{0}" pattern'.format(pattern))

    config.setdefault('packageFiles', [])
    config['packageFiles'] += files


def updateEnvFromOutput(env_to_set):
    environ = _ext.os.environ
    env_to_set = env_to_set.split("\n")

    for e in env_to_set:
        if not e:
            continue
        n, v = e.split('=', 1)
        environ[n] = v


def userHome():
    return _ext.os.environ['HOME']


def deployHome():
    environ = _ext.os.environ
    return environ.get('CID_DEPLOY_HOME', environ['HOME'])


def loadJSONConfig(file_name, defvalue=None):
    if _ext.ospath.exists(file_name):
        with open(file_name, 'r') as content_file:
            content = content_file.read()
            return _ext.configutil.parseJSON(content)
    else:
        return defvalue


def updateJSONConfig(file_name, updater, indent=2, separators=(',', ': ')):
    content = loadJSONConfig(file_name)

    if content is None:
        return []

    updater(content)

    writeJSONConfig(file_name, content, indent, separators)

    return [file_name]


def writeJSONConfig(file_name, content, indent=2, separators=(',', ': ')):
    with open(file_name, 'w') as content_file:
        content = _ext.json.dumps(
            content, indent=indent, separators=separators)
        content_file.write(content)
        content_file.write("\n")

# ---


def readTextFile(file_name):
    with open(file_name, 'r') as content_file:
        return content_file.read()


def updateTextFile(file_name, updater):
    content = readTextFile(file_name)
    content = updater(content)
    writeTextFile(file_name, content)

    return [file_name]


def writeTextFile(file_name, content):
    with open(file_name, 'w') as content_file:
        content_file.write(content)


def writeBinaryFile(file_name, content):
    content = _ext.executil.toBytes(content)

    with open(file_name, 'wb') as content_file:
        content_file.write(content)


def writeIni(file_name, content):
    str_content = []
    listify = _ext.configutil.listify

    for (sn, sv) in content.items():
        str_content.append('[{0}]'.format(sn))

        for (cn, cv) in sv.items():
            for cvi in listify(cv):
                str_content.append('{0} = {1}'.format(cn, cvi))

        str_content.append('')

    str_content = "\n".join(str_content)
    writeTextFile(file_name, str_content)


def mkDir(dir):
    try:
        _ext.os.makedirs(dir)
    except OSError:
        if not _ext.ospath.exists(dir):
            raise


def rmTree(dir, verbose=True):
    stat = _ext.stat

    if not _ext.ospath.exists(dir):
        return

    if verbose:
        _log.infoLabel('Removing: ', dir)

    chmodTree(dir, stat.S_IRWXU, stat.S_IRUSR | stat.S_IWUSR)

    if _ext.ospath.isdir(dir):
        _ext.shutil.rmtree(dir)
    else:
        _ext.os.unlink(dir)


def chmodTree(dir, dperm, fperm, keep_execute=False):
    os = _ext.os
    ospath = _ext.ospath
    stat = _ext.stat

    st_mode = os.lstat(dir).st_mode

    if stat.S_ISLNK(st_mode):
        lchmod(dir, fperm)
        return
    elif not stat.S_ISDIR(st_mode):
        os.chmod(dir, fperm)
        return

    walk_list = os.walk(dir)
    os.chmod(dir, dperm)

    for (path, dirs, files) in walk_list:
        for f in dirs + files:
            f = os.path.join(path, f)

            st_mode = os.lstat(f).st_mode

            if stat.S_ISLNK(st_mode):
                lchmod(f, fperm)
                continue

            if stat.S_ISDIR(st_mode):
                os.chmod(f, dperm)
            elif keep_execute:
                xperm = st_mode & (stat.S_IXUSR | stat.S_IXGRP)
                os.chmod(f, fperm | xperm)
            else:
                os.chmod(f, fperm)


def lchmod(target, perm):
    lchmod = getattr(_ext.os, 'lchmod', None)

    if lchmod:
        try:
            lchmod(target, perm)
        except OSError as e:
            # lchmod is falsely available in some Linux builds
            if e.errno != _ext.errno.ENOTSUP:
                raise


def cacheDir(key):
    os = _ext.os
    cache_dir = os.path.join(
        os.environ['HOME'], '.cache', 'futoin-cid', key)

    mkDir(cache_dir)

    return cache_dir


def tmpCacheDir(**kwargs):
    os = _ext.os
    stat = _ext.stat
    tmp_dir = cacheDir('tmp')

    # do once a day
    base_ts = int(_ext.time.time()) - (24 * 60 * 60)
    placeholder = os.path.join(tmp_dir, 'cleanup.stamp')

    if os.path.exists(placeholder) and os.stat(placeholder).st_mtime > base_ts:
        pass
    else:
        for f in os.listdir(tmp_dir):
            fp = os.path.join(tmp_dir, f)
            s = os.stat(fp)

            if s.st_mtime <= base_ts:
                if stat.S_ISDIR(s.st_mode):
                    _ext.pathutil.rmTree(fp)
                else:
                    os.remove(fp)
        _ext.pathutil.writeTextFile(placeholder, '')

    return _ext.tempfile.mkdtemp(dir=tmp_dir, **kwargs)


def downloadFile(env, url, dst):
    dst_tmp = dst + '.tmp'

    rmTree(dst_tmp)
    rmTree(dst)

    kwargs = {}
    _ext.configutil.requestsOptions(env, kwargs)
    kwargs['stream'] = True
    res = _ext.requests.request('GET', url, **kwargs)
    res.raise_for_status()

    with open(dst_tmp, 'wb') as f:
        _ext.shutil.copyfileobj(res.raw, f)

    _ext.os.rename(dst_tmp, dst)


def cacheDownloadFile(env, url):
    ospath = _ext.ospath
    url_hash = _ext.hashlib.sha256(url.encode('utf8')).hexdigest()
    cache_dir = _ext.pathutil.cacheDir('dl_{0}'.format(url_hash))
    cache_file = ospath.join(cache_dir, url.split('/')[-1])

    if not ospath.exists(cache_file):
        downloadFile(env, url, cache_file)

    return cache_file


def downloadStream(env, url, cmd):
    kwargs = {}
    _ext.configutil.requestsOptions(env, kwargs)
    kwargs['stream'] = True
    res = _ext.requests.request('GET', url, **kwargs)
    res.raise_for_status()

    _ext.executil.callExternal(cmd, input_stream=res.raw)


def downloadExtract(env, url, dst, tar_algo, strip=0):
    dst_tmp = dst + '.tmp'

    rmTree(dst_tmp)
    rmTree(dst)

    _ext.os.makedirs(dst_tmp)
    cmd = ['tar', 'x' + tar_algo, '-C', dst_tmp]

    if strip:
        cmd += ['--strip-components={0}'.format(strip)]

    downloadStream(env, url, cmd)
    _ext.os.rename(dst_tmp, dst)
