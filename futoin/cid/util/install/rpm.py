
from ...mixins.ondemand import ext as _ext

_yum = _ext.pathutil.which('yum')
_dnf = _ext.pathutil.which('dnf')
_zypper = _ext.pathutil.which('zypper')
_rpm = _ext.pathutil.which('rpm')


def yum(packages):
    yum = _dnf or _yum

    if yum:
        packages = _ext.configutil.listify(packages)

        _ext.executil.trySudoCall(
            [yum, 'install', '-y'] + packages,
            errmsg='you may need to install the packages manually !'
        )


def zypper(packages):
    if _zypper:
        packages = _ext.configutil.listify(packages)

        _ext.executil.trySudoCall(
            [_zypper, 'install', '-y'] + packages,
            errmsg='you may need to install the packages manually !'
        )


def rpm(packages):
    yum(packages)
    zypper(packages)


def rpmKey(gpg_key):
    if not gpg_key:
        return

    if not _rpm:
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
    rpmKey(gpg_key)

    repo_file = None
    repo_info = None
    pathutil = _ext.pathutil

    #---
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

    #---
    try:
        dist_ver = _ext.detect.linuxDistVersion().split('.')[0]

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

        #---
        if _dnf:
            yum(['dnf-plugins-core'])
            _ext.executil.trySudoCall(
                [_dnf, 'config-manager', '--add-repo', url],
                errmsg='you may need to add the repo manually!'
            )

        elif _yum:
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
    rpmKey(gpg_key)

    if _zypper:
        if yum:
            cmd = [_zypper, 'addrepo', '-t', 'YUM', url, name]
        else:
            cmd = [_zypper, 'addrepo', url, name]

        _ext.executil.trySudoCall(
            cmd,
            errmsg='you may need to add the repo manually!'
        )


def yumEnable(repo):
    if _dnf:
        yum(['dnf-plugins-core'])
        _ext.executil.trySudoCall(
            [_dnf, 'config-manager', '--enable', repo],
            errmsg='you may need to add the repo manually!'
        )

    elif _yum:
        yum(['yum-utils'])

        yumcfgmgr = _ext.pathutil.which('yum-config-manager')

        _ext.executil.trySudoCall(
            [yumcfgmgr, '--enable', repo],
            errmsg='You may need to enable the repo manually'
        )


def yumEPEL():
    detect = _ext.detect

    if detect.isOracleLinux() or detect.isRHEL():
        ver = _ext.detect.linuxDistVersion().split('.')[0]
        yum(
            ['https://dl.fedoraproject.org/pub/epel/epel-release-latest-{0}.noarch.rpm'.format(ver)])
    else:
        yum(['epel-release'])


def yumSCL():
    detect = _ext.detect

    if not detect.isSCLSupported():
        return

    ver = _ext.detect.linuxDistVersion().split('.')[0]

    if detect.isRHEL():
        yumEnable('rhel-server-rhscl-{0}-rpms'.format(ver))
    elif detect.isCentOS():
        yum('centos-release-scl-rh')
    elif detect.isOracleLinux():
        yumRepo('public-yum-o1{0}'.format(ver),
                'http://yum.oracle.com/public-yum-ol{0}.repo'.format(ver))
        yumEnable('ol{0}_software_collections'.format(ver))
        yumEnable('ol{0}_latest'.format(ver))
        yumEnable('ol{0}_optional_latest'.format(ver))

    yum('scl-utils')


def yumIUS():
    detect = _ext.detect

    if not detect.isSCLSupported():
        return

    yumEPEL()
    ver = _ext.detect.linuxDistVersion().split('.')[0]

    if detect.isCentOS():
        yum('https://centos{0}.iuscommunity.org/ius-release.rpm'.format(ver))
    else:
        yum('https://rhel{0}.iuscommunity.org/ius-release.rpm'.format(ver))
