
from __future__ import print_function, absolute_import

import os
import sys
import subprocess
import glob


class PathMixIn(object):
    _dev_null = None

    def _callExternal(self, cmd, suppress_fail=False, verbose=True,
                      output_handler=None, input=False,
                      merge_stderr=False, cwd=None,
                      user_interaction=False,
                      encoding='UTF-8',
                      binary_input=False, binary_output=False):
        try:
            if not PathMixIn._dev_null:
                PathMixIn._dev_null = open(os.devnull, 'w')

            if input:
                stdin = subprocess.PIPE
            elif user_interaction:
                stdin = None
            else:
                stdin = PathMixIn._dev_null

            if merge_stderr:
                stderr = subprocess.STDOUT
            elif verbose and not suppress_fail:
                self._info(subprocess.list2cmdline(cmd), 'Call: ')
                sys.stdout.flush()
                sys.stderr.flush()
                stderr = sys.stderr
            else:
                stderr = PathMixIn._dev_null

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

    def _callInteractive(self, cmd, replace=True, *args, **kwargs):
        if replace:
            if args or kwargs:
                self._errorExit(
                    'Extra args are not supported for replace call')

            self._info(subprocess.list2cmdline(cmd), 'Exec: ')
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
            self._callExternal(cmd, user_interaction=True, *args, **kwargs)

    def _trySudoCall(self, cmd, errmsg=None, **kwargs):
        try:
            if self._isAdmin():
                self._callExternal(cmd, **kwargs)
                return

            self._callExternal(['sudo', '-n', '-H'] + cmd, **kwargs)
        except subprocess.CalledProcessError:
            if not errmsg:
                errmsg = 'you may need to call the the failed command manually !'

            self._warn(errmsg)

    def _which(self, program):
        "Copied from stackoverflow"
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file

        return None

    def _addEnvPath(self, env_name, add_dir, first=False):
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

    def _delEnvPath(self, env_name, del_dir, fail=False):
        if env_name in os.environ:
            dir_list = os.environ[env_name].split(os.pathsep)

            try:
                del dir_list[dir_list.index(del_dir)]
            except ValueError:
                if fail:
                    raise
        elif fail:
            # trigger KeyError
            return os.environ[env_name]

    def _addBinPath(self, bin_dir, first=False):
        self._addEnvPath('PATH', bin_dir, first=first)

    def _addPackageFiles(self, config, pattern):
        files = glob.glob(pattern)

        if not files:
            self._errorExit(
                'Failed to find created packages of "{0}" pattern'.format(pattern))

        config.setdefault('packageFiles', [])
        config['packageFiles'] += files

    def _deployHome(self):
        return os.environ.get('CID_DEPLOY_HOME', os.environ['HOME'])
