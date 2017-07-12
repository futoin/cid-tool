
from ...mixins.ondemand import ext as _ext


def emerge(packages):
    if not _ext.detect.isEmerge():
        return

    emerge = _ext.pathutil.which('emerge')

    packages = _ext.configutil.listify(packages)

    _ext.executil.trySudoCall(
        [emerge] + packages,
        errmsg='you may need to install the build deps manually !'
    )


def emergeDepsOnly(packages):
    packages = _ext.configutil.listify(packages)
    emerge(['--onlydeps'] + packages)
