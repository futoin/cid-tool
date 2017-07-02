
from ...mixins.ondemand import ext as _ext

_emerge = _ext.pathutil.which('emerge')


def emerge(packages):
    if _emerge:
        if not isinstance(packages, list):
            packages = [packages]

        _ext.executil.trySudoCall(
            [_emerge] + packages,
            errmsg='you may need to install the build deps manually !'
        )


def emergeDepsOnly(packages):
    if not isinstance(packages, list):
        packages = [packages]

    emerge(['--onlydeps'] + packages)
