
from ..mixins.ondemand import ext as _ext
from . import log as _log

_dev_null = None


def devNull():
    g = globals()
    ret = g['_dev_null']

    if ret is None:
        ret = open(_ext.os.devnull, 'w')
        g['_dev_null'] = ret

    return ret


def callExternal(cmd, suppress_fail=False, verbose=True,
                 output_handler=None, input=False,
                 merge_stderr=False, cwd=None,
                 user_interaction=False,
                 encoding='UTF-8',
                 binary_input=False, binary_output=False):

    sys = _ext.sys
    subprocess = _ext.subprocess

    if verbose and not suppress_fail:
        _log.infoLabel('Call: ', subprocess.list2cmdline(cmd))
        sys.stdout.flush()
        sys.stderr.flush()

    try:
        if input:
            stdin = subprocess.PIPE
        elif user_interaction:
            stdin = None
        else:
            stdin = devNull()

        if merge_stderr:
            stderr = subprocess.STDOUT
        elif verbose and not suppress_fail:
            stderr = sys.stderr
        else:
            stderr = devNull()

        if user_interaction and not output_handler:
            stdout = None
        else:
            stdout = subprocess.PIPE

        chunk_size = 65536
        res_buffers = []
        p = subprocess.Popen(cmd, stdin=stdin, stderr=stderr,
                             bufsize=chunk_size * 2, close_fds=True,
                             stdout=stdout, cwd=cwd)

        if input:
            if not binary_input:
                input = input.encode(encoding=encoding)

            try:
                p.stdin.write(input)
                p.stdin.flush()
            finally:
                p.stdin.close()

        if stdout:
            if output_handler:
                on_chunk = output_handler
            elif binary_output:
                def on_binary_chunk(x):
                    res_buffers.append(x)

                on_chunk = on_binary_chunk
            else:
                def on_str_chunk(x):
                    try:
                        x = str(x, encoding)
                    except TypeError:
                        pass

                    res_buffers.append(x)

                on_chunk = on_str_chunk

            try:
                while True:
                    chunk = p.stdout.read(chunk_size)

                    if chunk:
                        on_chunk(chunk)
                    else:
                        break
            finally:
                while p.stdout.read(chunk_size):
                    pass

        p.wait()

        if binary_output:
            res = b''.join(res_buffers)
        else:
            res = ''.join(res_buffers)

        if p.returncode != 0:
            raise subprocess.CalledProcessError(p.returncode, cmd, res)

        return res
    except subprocess.CalledProcessError:
        if suppress_fail:
            return None
        raise


def callInteractive(cmd, replace=True, *args, **kwargs):
    if replace:
        if args or kwargs:
            _log.errorExit(
                'Extra args are not supported for replace call')

        sys = _ext.sys
        subprocess = _ext.subprocess
        os = _ext.os

        _log.infoLabel('Exec: ', subprocess.list2cmdline(cmd))
        sys.stdout.flush()
        sys.stderr.flush()

        # There is a problem of left FDs in Python 2
        #---
        import resource

        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]

        if (maxfd == resource.RLIM_INFINITY):
            maxfd = 10240

        for fd in range(3, maxfd):
            try:
                os.close(fd)
            except OSError:
                pass
        #---

        os.execv(cmd[0], cmd)
    else:
        callExternal(cmd, user_interaction=True, *args, **kwargs)


def trySudoCall(cmd, errmsg=None, **kwargs):
    try:
        if _ext.detect.isAdmin():
            callExternal(cmd, **kwargs)
            return

        callExternal(['sudo', '-n', '-H'] + cmd, **kwargs)
    except _ext.subprocess.CalledProcessError:
        if not errmsg:
            errmsg = 'you may need to call the the failed command manually !'

        _log.warn(errmsg)


def startService(name):
    openrc = '/sbin/rc-service'
    systemctl = '/bin/systemctl'
    ospath = _ext.ospath

    if ospath.exists(systemctl):
        trySudoCall(
            [systemctl, 'start', name],
            errmsg='you may need to start the service manually')
    elif ospath.exists(openrc):
        trySudoCall(
            [openrc, name, 'start'],
            errmsg='you may need to start the service manually')
