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

from ...mixins.ondemand import ext as _ext

_yum = _ext.pathutil.which('yum')
_dnf = _ext.pathutil.which('dnf')
_zypper = _ext.pathutil.which('zypper')
_rpm = _ext.pathutil.which('rpm')


def yum(packages):
    if not _ext.detect.isYum() and not _ext.detect.isDnf():
        return

    yum = _dnf or _yum

    packages = _ext.configutil.listify(packages)

    _ext.executil.trySudoCall(
        [yum, 'install', '-y'] + packages,
        errmsg='you may need to install the packages manually !'
    )


def zypper(packages):
    if not _ext.detect.isZypper():
        return

    packages = _ext.configutil.listify(packages)

    _ext.executil.trySudoCall(
        [_zypper, '--non-interactive', 'install', '-y'] + packages,
        errmsg='you may need to install the packages manually !'
    )


def rpm(packages):
    yum(packages)
    zypper(packages)


def rpmKey(gpg_key):
    if not gpg_key:
        return

    if not _ext.detect.isRPM():
        return

    os = _ext.os

    tmp_dir = _ext.pathutil.tmpCacheDir(prefix='cidgpg')
    tf = os.path.join(tmp_dir, 'key.gpg')
    _ext.pathutil.writeBinaryFile(tf, gpg_key)

    _ext.executil.trySudoCall(
        [_rpm, '--import', tf],
        errmsg='you may need to import the PGP key manually!'
    )

    os.remove(tf)


def yumRepo(name, url, gpg_key=None, releasevermax=None, repo_url=False):
    if not _ext.detect.isYum() and not _ext.detect.isDnf():
        return

    rpmKey(gpg_key)

    repo_file = None
    repo_info = None
    pathutil = _ext.pathutil

    # ---
    if repo_url:
        tmp_dir = pathutil.tmpCacheDir(prefix='cidrepo')
        repo_file = '{0}.repo'.format(name)
        repo_file = _ext.ospath.join(tmp_dir, repo_file)

        repo_info = "\n".join([
            '[nginx]',
            'name={0} repo'.format(name),
            'baseurl={0}'.format(url),
            'gpgcheck=1',
            'enabled=1',
            ''
        ])

        pathutil.writeTextFile(repo_file, repo_info)
        url = repo_file

    # ---
    try:
        dist_ver = _ext.detect.linuxDistMajorVer()

        if releasevermax is not None and int(dist_ver) > releasevermax:
            dist_ver = releasevermax

            if not repo_info:
                repo_info = _ext.urllib.urlopen(url).read()
                repo_info = _ext.executil.toString(repo_info)

            repo_info = repo_info.replace('$releasever', str(dist_ver))

            if not repo_file:
                tmp_dir = _ext.pathutil.tmpCacheDir(prefix='cidrepo')
                repo_file = url.split('/')[-1]
                repo_file = _ext.ospath.join(tmp_dir, repo_file)

            pathutil.writeTextFile(repo_file, repo_info)
            url = repo_file

        # ---
        if _dnf:
            yum(['dnf-plugins-core'])
            _ext.executil.trySudoCall(
                [_dnf, 'config-manager', '--add-repo', url],
                errmsg='you may need to add the repo manually!'
            )

        else:
            yum(['yum-utils'])
            yumcfgmgr = _ext.pathutil.which('yum-config-manager')
            _ext.executil.trySudoCall(
                [yumcfgmgr, '--add-repo', url],
                errmsg='you may need to add the repo manually!'
            )
    finally:
        if repo_file:
            _ext.pathutil.rmTree(repo_file)


def zypperRepo(name, url, gpg_key=None, yum=False):
    if not _ext.detect.isZypper():
        return

    rpmKey(gpg_key)

    if yum:
        cmd = [_zypper, '--non-interactive', 'addrepo', '-t', 'YUM', url, name]
    elif name:
        cmd = [_zypper, '--non-interactive', 'addrepo', url, name]
    else:
        cmd = [_zypper, '--non-interactive', 'addrepo', url]

    _ext.executil.trySudoCall(
        cmd,
        errmsg='you may need to add the repo manually!'
    )

    if name:
        _ext.executil.trySudoCall(
            [_zypper, '--non-interactive', 'refresh', '-r', name],
            errmsg='you may need to add the repo manually!'
        )
    else:
        _ext.executil.trySudoCall(
            [_zypper, '--non-interactive', 'refresh'],
            errmsg='you may need to add the repo manually!'
        )


def yumEnable(repo):
    if _ext.detect.isDnf():
        yum(['dnf-plugins-core'])
        _ext.executil.trySudoCall(
            [_dnf, 'config-manager', '--enable', repo],
            errmsg='you may need to add the repo manually!'
        )

    elif _ext.detect.isYum():
        yum(['yum-utils'])

        yumcfgmgr = _ext.pathutil.which('yum-config-manager')

        _ext.executil.trySudoCall(
            [yumcfgmgr, '--enable', repo],
            errmsg='You may need to enable the repo manually'
        )


def yumEPEL():
    detect = _ext.detect

    if not detect.isRPM():
        return

    if detect.isCentOS():
        yum(['epel-release'])
    else:
        ver = detect.linuxDistMajorVer()
        yum(
            ['https://dl.fedoraproject.org/pub/epel/epel-release-latest-{0}.noarch.rpm'.format(ver)])


def yumSCL():
    detect = _ext.detect

    if not detect.isSCLSupported():
        return

    ver = detect.linuxDistMajorVer()

    if detect.isRHEL():
        yumEnable('rhel-server-rhscl-{0}-rpms'.format(ver))
    elif detect.isCentOS():
        yum('centos-release-scl-rh')
    elif detect.isOracleLinux():
        yumOLPublic([
            'software_collections',
            'latest',
            'optional_latest',
        ])

    yum('scl-utils')


def yumIUS():
    detect = _ext.detect

    if not detect.isSCLSupported():
        return

    yumEPEL()
    ver = detect.linuxDistMajorVer()

    if detect.isCentOS():
        yum('https://centos{0}.iuscommunity.org/ius-release.rpm'.format(ver))
    else:
        yum('https://rhel{0}.iuscommunity.org/ius-release.rpm'.format(ver))


def yumRHELRepo(repos):
    detect = _ext.detect

    if not detect.isRHEL():
        return

    ver = detect.linuxDistMajorVer()
    repos = _ext.configutil.listify(repos)

    scrmgr = _ext.pathutil.which('subscription-manager')

    for r in repos:
        _ext.executil.trySudoCall(
            [scrmgr, 'repos', '--enable', 'rhel-{0}-{1}'.format(ver, r)],
            errmsg='you may need to enable the repo manually!'
        )


def yumOLPublic(repos):
    detect = _ext.detect

    if not detect.isOracleLinux():
        return

    ver = detect.linuxDistMajorVer()
    repos = _ext.configutil.listify(repos)

    if not _ext.ospath.exists('/etc/yum.repos.d/public-yum-ol{0}.repo'.format(ver)):
        yumRepo('public-yum-o1{0}'.format(ver),
                'http://yum.oracle.com/public-yum-ol{0}.repo'.format(ver))

    for r in repos:
        yumEnable('ol{0}_{1}'.format(ver, r))


def SUSEConnect(ext):
    if not _ext.detect.isSLES():
        return

    _ext.executil.trySudoCall(
        ['/usr/bin/SUSEConnect', '--product', ext, '-r', ''],
        errmsg='you may need to add the extension manually!'
    )


def SUSEConnectVerArch(ext, full_ver=False):
    detect = _ext.detect

    if not detect.isSLES():
        return

    if full_ver:
        sles_ver = detect.osRelease()
    else:
        sles_ver = detect.linuxDistMajorVer()

    base_arch = detect.basearch()
    SUSEConnect('{0}/{1}/{2}'.format(ext, sles_ver, base_arch))
