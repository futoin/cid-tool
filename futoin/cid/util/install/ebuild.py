
from ...mixins.ondemand import ext as _ext


def emerge(packages):
    emerge = _ext.path.which('emerge')

    if emerge:
        if not isinstance(packages, list):
            packages = [packages]

        _ext.exec.trySudoCall(
            [emerge] + packages,
            errmsg='you may need to install the build deps manually !'
        )


def emergeDepsOnly(packages):
    if not isinstance(packages, list):
        packages = [packages]

    emerge(['--onlydeps'] + packages)
