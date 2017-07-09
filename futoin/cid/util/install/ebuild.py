
from ...mixins.ondemand import ext as _ext

_emerge = _ext.pathutil.which('emerge')


def emerge(packages):
    if _emerge:
        packages = _ext.configutil.listify(packages)

        _ext.executil.trySudoCall(
            [_emerge] + packages,
            errmsg='you may need to install the build deps manually !'
        )


def emergeDepsOnly(packages):
    packages = _ext.configutil.listify(packages)
    emerge(['--onlydeps'] + packages)
