
from ...mixins.ondemand import ext as _ext
from .. import log as _log


def deb(packages):
    apt_get = _ext.pathutil.which('apt-get')

    if apt_get:
        packages = _ext.configutil.listify(packages)

        _ext.os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
        _ext.executil.trySudoCall(
            [apt_get, 'install', '-y',
                '--no-install-recommends',
                '-o', 'Dpkg::Options::=--force-confdef',
                '-o', 'Dpkg::Options::=--force-confold'] + packages,
            errmsg='you may need to install the packages manually !'
        )


def aptRepo(name, entry, gpg_key=None, codename_map=None, repo_base=None):
    deb([
        'software-properties-common',
        'apt-transport-https',
        'ca-certificates',
        'lsb-release',
    ])
    apt_add_repository = _ext.pathutil.which('apt-add-repository')

    if not apt_add_repository:
        return

    if gpg_key:
        try:
            gpg_key = gpg_key.encode(encoding='UTF-8')
        except:
            pass

        tmp_dir = _ext.pathutil.tmpCacheDir(prefix='cidgpg')
        tf = _ext.ospath.join(tmp_dir, 'key.gpg')
        _ext.pathutil.writeBinaryFile(tf, gpg_key)

        _ext.executil.trySudoCall(
            ['apt-key', 'add', tf],
            errmsg='you may need to import the PGP key manually!'
        )

        _ext.os.remove(tf)

    codename = _ext.detect.osCodeName()

    if codename_map:
        try:
            repo_info = _ext.urllib.urlopen(
                '{0}/{1}'.format(repo_base, codename)).read()
        except:
            fallback_codename = codename_map.get(codename, codename)
            _log.warn('Fallback to codename: {0}'.format(
                fallback_codename))
            codename = fallback_codename

    entry = entry.replace('$codename$', codename)

    _ext.executil.trySudoCall(
        [apt_add_repository, '--yes', entry],
        errmsg='you may need to add the repo manually!'
    )

    _ext.executil.trySudoCall(
        ['apt-get', 'update'],
        errmsg='you may need to update APT cache manually!'
    )
