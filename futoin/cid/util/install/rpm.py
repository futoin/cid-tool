
from ...mixins.ondemand import ext as _ext


def yum(packages):
    yum = _ext.path.which('dnf')

    if not yum:
        yum = _ext.path.which('yum')

    if yum:
        if not isinstance(packages, list):
            packages = [packages]

        _ext.exec.trySudoCall(
            [yum, 'install', '-y'] + packages,
            errmsg='you may need to install the packages manually !'
        )


def zypper(packages):
    zypper = _ext.path.which('zypper')

    if zypper:
        if not isinstance(packages, list):
            packages = [packages]

        _ext.exec.trySudoCall(
            [zypper, 'install', '-y'] + packages,
            errmsg='you may need to install the packages manually !'
        )


def rpm(packages):
    yum(packages)
    zypper(packages)


def rpmKey(gpg_key):
    if not gpg_key:
        return

    rpm = _ext.path.which('rpm')

    if not rpm:
        return

    os = _ext.os

    tmp_dir = _ext.path.tmpCacheDir(prefix='cidgpg')
    tf = os.path.join(tmp_dir, 'key.gpg')
    _ext.path.writeBinaryFile(tf, gpg_key)

    _ext.exec.trySudoCall(
        [rpm, '--import', tf],
        errmsg='you may need to import the PGP key manually!'
    )

    os.remove(tf)


def yumRepo(name, url, gpg_key=None, releasevermax=None, repo_url=False):
    rpmKey(gpg_key)

    dnf = _ext.path.which('dnf')
    yum = _ext.path.which('yum')

    if repo_url:
        tmp_dir = _ext.path.tmpCacheDir(prefix='cidrepo')
        repo_file = '{0}.repo'.format(name)
        repo_file = _ext.ospath.join(tmp_dir, repo_file)

        with open(repo_file, 'w') as f:
            f.write("\n".join([
                '[nginx]',
                'name={0} repo'.format(name),
                'baseurl={0}'.format(url),
                'gpgcheck=1',
                'enabled=1',
                ''
            ]))

        url = repo_file

    if dnf:
        yum(['dnf-plugins-core'])
        repo_file = None

        if releasevermax is not None:
            dump = _ext.exec.callExternal(
                [dnf, 'config-manager', '--dump'], verbose=False)
            for l in dump.split("\n"):
                l = l.split(' = ')

                if l[0] == 'releasever':
                    if int(l[1]) > releasevermax:
                        repo_info = _ext.urllib.urlopen(url).read()

                        try:
                            repo_info = str(repo_info, 'utf8')
                        except:
                            pass

                        repo_info = repo_info.replace(
                            '$releasever', str(releasevermax))

                        tmp_dir = _ext.path.tmpCacheDir(prefix='cidrepo')
                        repo_file = url.split('/')[-1]
                        repo_file = _ext.ospath.join(tmp_dir, repo_file)

                        with open(repo_file, 'w') as f:
                            f.write(repo_info)

                        url = repo_file
                    break

        _ext.exec.trySudoCall(
            [dnf, 'config-manager', '--add-repo', url],
            errmsg='you may need to add the repo manually!'
        )

        if repo_file:
            _ext.os.remove(repo_file)

    elif yum:
        yum(['yum-utils'])
        yumcfgmgr = _ext.path.which('yum-config-manager')
        _ext.exec.trySudoCall(
            [yumcfgmgr, '--add-repo', url],
            errmsg='you may need to add the repo manually!'
        )


def zypperRepo(name, url, gpg_key=None, yum=False):
    rpmKey(gpg_key)

    zypper = _ext.path.which('zypper')

    if zypper:
        if yum:
            cmd = [zypper, 'addrepo', '-t', 'YUM', url, name]
        else:
            cmd = [zypper, 'addrepo', url, name]

        _ext.exec.trySudoCall(
            cmd,
            errmsg='you may need to add the repo manually!'
        )


def yumEnable(repo):
    yum(['yum-utils'])

    yumcfgmgr = _ext.path.which('yum-config-manager')

    _ext.exec.trySudoCall(
        [yumcfgmgr, '--enable', repo],
        errmsg='You may need to enable the repo manually'
    )


def yumEPEL():
    detect = _ext.detect

    if detect.isOracleLinux() or detect.isRHEL():
        ver = _ext.platform.linux_distribution()[1].split('.')[0]
        yum(
            ['https://dl.fedoraproject.org/pub/epel/epel-release-latest-{0}.noarch.rpm'.format(ver)])
    else:
        yum(['epel-release'])


def yumSCL():
    detect = _ext.detect

    if detect.isRHEL():
        yumEnable('rhel-server-rhscl-7-rpms')
    elif detect.isCentOS():
        yum('centos-release-scl-rh')
    elif detect.isOracleLinux():
        yumRepo('public-yum-o17',
                'http://yum.oracle.com/public-yum-ol7.repo')
        yumEnable('ol7_software_collections')
        yumEnable('ol7_latest')
        yumEnable('ol7_optional_latest')

    yum('scl-utils')
