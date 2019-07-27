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

from .data import DataSlots


class TimeoutException(RuntimeError):
    __slots__ = ()

    @classmethod
    def alarmHandler(cls, *args, **kwargs):
        raise TimeoutException('Alarm')


class ServiceMixIn(DataSlots):
    __slots__ = ()

    __MASTER_PID_FILE = '.futoin.master.pid'
    __RESTART_DELAY = 10
    __RESTART_DELAY_THRESHOLD = __RESTART_DELAY * 2

    def _serviceAdapt(self):
        if not self._config['adaptDeploy']:
            return

        self._deployLock()
        try:
            self._deploy_setup()
        finally:
            self._deployUnlock()

    def _serviceList(self):
        self._deployLock()
        try:
            self._initConfig()
        finally:
            self._deployUnlock()

        return self._configServiceList(self._config)

    def _configServiceList(self, config):
        entry_points = config.get('entryPoints', {})
        auto_services = config.get('deploy', {}).get('autoServices', {})
        tool_tune = config.get('toolTune', {})
        res = []

        deepCopy = self._ext.copy.deepcopy
        deepMerge = self._configutil.deepMerge

        for (ep, ei) in entry_points.items():
            if ep not in auto_services:
                self._errorExit(
                    'Unknown service entry point "{0}"'.format(ep))

            i = 0

            for svctune in auto_services[ep]:
                r = deepCopy(ei)
                r['name'] = ep
                r['instanceId'] = i
                r_tune = deepCopy(tool_tune.get(r['tool'], {}))
                deepMerge(r_tune, r.get('tune', {}))
                deepMerge(r_tune, svctune)

                internal = r_tune.get('internal', False)

                if internal and r_tune.get('socketType', None) != 'unix':
                    r_sockaddr = r_tune.get('socketAddress', None)

                    if r_sockaddr == '0.0.0.0':
                        r_tune['socketAddress'] = '127.0.0.1'
                    elif r_sockaddr == '::':
                        r_tune['socketAddress'] = '::1'

                r['tune'] = r_tune

                res.append(r)
                i += 1

        return res

    def _serviceListPrint(self):
        for svc in self._serviceList():
            svc_tune = svc['tune']

            # ---
            internal = svc_tune.get('internal', False)

            if not internal:
                internal = not bool(svc_tune.get('socketType', False))

            if internal:
                print("{0}\t{1}".format(svc['name'], svc['instanceId']))
                continue

            # ---
            socket_type = svc_tune['socketType']

            if socket_type == 'unix':
                socket_addr = svc_tune['socketPath']
            elif socket_type == 'tcp6':
                socket_addr = '[{0}]:{1}'.format(
                    svc_tune['socketAddress'],
                    svc_tune['socketPort']
                )
            else:
                socket_addr = '{0}:{1}'.format(
                    svc_tune['socketAddress'],
                    svc_tune['socketPort']
                )

            print("\t".join([svc['name'], str(svc['instanceId']),
                             socket_type, socket_addr]))

    def _serviceCommon(self, entry_point, instance_id):
        config = self._config
        entry_points = config.get('entryPoints', {})
        auto_services = config.get('deploy', {}).get('autoServices', {})

        try:
            instance_id = int(instance_id)
        except ValueError:
            self._errorExit('Invalid instance ID "{0}"'.format(instance_id))

        try:
            ep = entry_points[entry_point]
        except KeyError:
            self._errorExit('Unknown entry point "{0}"'.format(entry_point))

        try:
            dep = auto_services[entry_point][instance_id]
        except KeyError:
            self._errorExit(
                'Unknown service entry point "{0}"'.format(entry_point))
        except IndexError:
            self._errorExit('Unknown service entry point "{0}" instance "{1}"'.format(
                entry_point, instance_id))

        res = self._ext.copy.deepcopy(ep)
        res.setdefault('tune', {}).update(dep)
        res['name'] = entry_point
        res['instanceId'] = instance_id
        return res

    def _serviceStop(self, svc, toolImpl, pid):
        signal = self._ext.signal
        os = self._os
        from ..runtimetool import RuntimeTool

        signal.signal(signal.SIGALRM, TimeoutException.alarmHandler)

        tune = svc['tune']

        try:
            toolImpl.onStop(self._config, pid, tune)
        except Exception as e:
            self._warn(str(e))
            return

        try:
            timeout = tune.get(
                'exitTimeoutMS', RuntimeTool.DEFAULT_EXIT_TIMEOUT)
            timeout /= 1000.0
            signal.setitimer(signal.ITIMER_REAL, timeout)

            try:
                os.waitpid(pid, 0)
            except TimeoutException:
                signal.setitimer(signal.ITIMER_REAL, 0)
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
        except OSError:
            pass
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def _serviceMasterPID(self):
        self._requireDeployLock()

        if not self._ospath.exists(self.__MASTER_PID_FILE):
            return None

        try:
            pid = int(self._pathutil.readTextFile(self.__MASTER_PID_FILE))
        except ValueError:
            return None

        try:
            self._masterLock()
            self._masterUnlock()
            return None
        except:
            pass

        return pid

    def _serviceMaster(self):
        signal = self._ext.signal
        os = self._os
        sys = self._sys
        time = self._ext.time
        from ..runtimetool import RuntimeTool

        svc_list = []
        pid_to_svc = {}

        self._running = True
        self._reload_services = True
        self._interruptable = False

        def serviceExitSignal(*args, **kwargs):
            self._running = False
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            signal.signal(signal.SIGHUP, signal.SIG_IGN)
            signal.signal(signal.SIGUSR1, signal.SIG_IGN)
            signal.signal(signal.SIGUSR2, signal.SIG_IGN)

            if self._interruptable:
                raise KeyboardInterrupt('Exit received')

        def serviceReloadSignal(*args, **kwargs):
            self._reload_services = True

            if self._interruptable:
                raise KeyboardInterrupt('Reload received')

        signal.signal(signal.SIGTERM, serviceExitSignal)
        signal.signal(signal.SIGINT, serviceExitSignal)
        signal.signal(signal.SIGHUP, serviceExitSignal)
        signal.signal(signal.SIGUSR1, serviceReloadSignal)
        signal.signal(signal.SIGUSR2, serviceReloadSignal)
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)  # important for macOS

        # Still, it's not safe to assume processes continue
        # to run in set process group.
        # DO NOT use os.killpg()
        #os.setpgid(0, 0)

        # Main loop
        # ---
        self._deployLock()
        try:
            current_master = self._serviceMasterPID()

            if current_master:
                self._errorExit(
                    'Master process is already running with PID "{0}"'.format(current_master))

            self._masterLock()
            self._pathutil.writeTextFile(self.__MASTER_PID_FILE,
                                         '{0}'.format(os.getpid()))
        finally:
            self._deployUnlock()

        self._info('Starting master process')
        self._dumpResourceStats()

        while self._running:
            # Reload services
            # ---
            if self._reload_services:
                self._info('Reloading services')

                # Mark shutdown by default
                for svc in svc_list:
                    svc['_remove'] = True

                # Prepare process list
                for newsvc in self._serviceList():
                    for svc in svc_list:
                        for (sk, sv) in newsvc.items():
                            if svc.get(sk, None) != sv:
                                break
                        else:
                            break
                    else:
                        svc = newsvc
                        svc_list.append(newsvc)
                        svc['_pid'] = None
                        svc['_lastExit1'] = self.__RESTART_DELAY_THRESHOLD + 1
                        svc['_lastExit2'] = 0

                        tool = svc['tool']
                        t = self._getTool(tool)

                        if not t.isInstalled(self._config['env']):
                            self._errorExit(
                                'Tool "{0}" for "{1}" is not installed'
                                .format(tool, newsvc['name']))
                        elif isinstance(t, RuntimeTool):
                            newsvc['toolImpl'] = t
                        else:
                            self._errorExit(
                                'Tool "{0}" for "{1}" is not of RuntimeTool type'
                                .format(tool, newsvc['name']))

                        self._info('Added "{0}:{1}"'.format(
                            svc['name'], svc['instanceId']))

                    svc['_remove'] = False

                if not len(svc_list):
                    break

                # Kill removed or changed services
                for svc in svc_list:
                    if svc['_remove']:
                        pid = svc['_pid']

                        if pid:
                            self._serviceStop(svc, svc['toolImpl'], pid)
                            pid_to_svc[pid]['_pid'] = None
                            del pid_to_svc[pid]

                        self._info('Removed "{0}:{1}" pid "{2}"'.format(
                            svc['name'], svc['instanceId'], pid))

                svc_list = list(filter(lambda v: not v['_remove'], svc_list))

                # actual reload of services
                for pid in pid_to_svc.keys():
                    svc = pid_to_svc[pid]

                    if svc['tune'].get('reloadable', False):
                        self._info('Reloading "{0}:{1}" pid "{2}"'.format(
                            svc['name'], svc['instanceId'], pid))
                        try:
                            svc['toolImpl'].onReload(
                                self._config, pid, svc['tune'])
                        except OSError:
                            pass
                    else:
                        self._info('Stopping "{0}:{1}" pid "{2}"'.format(
                            svc['name'], svc['instanceId'], pid))
                        self._serviceStop(svc, svc['toolImpl'], pid)

                        del pid_to_svc[pid]
                        svc['_lastExit1'] = self.__RESTART_DELAY_THRESHOLD + 1
                        svc['_lastExit2'] = 0
                        svc['_pid'] = None

                self._reload_services = False

            # create children
            for svc in svc_list:
                pid = svc['_pid']
                if pid:
                    continue

                delay = 0

                if (svc['_lastExit1'] - svc['_lastExit2']) < self.__RESTART_DELAY_THRESHOLD:
                    delay = self.__RESTART_DELAY

                pid = os.fork()

                if pid:
                    svc['_pid'] = pid
                    pid_to_svc[pid] = svc

                    if delay:
                        self._warn('Delaying start "{0}:{1}" pid "{2}"'.format(
                            svc['name'], svc['instanceId'], pid))
                    else:
                        self._info('Started "{0}:{1}" pid "{2}"'.format(
                            svc['name'], svc['instanceId'], pid))
                else:
                    try:
                        signal.signal(signal.SIGTERM, signal.SIG_DFL)
                        signal.signal(signal.SIGINT, signal.SIG_DFL)
                        signal.signal(signal.SIGHUP, signal.SIG_DFL)
                        signal.signal(signal.SIGUSR1, signal.SIG_DFL)
                        signal.signal(signal.SIGUSR2, signal.SIG_DFL)
                        signal.signal(signal.SIGCHLD, signal.SIG_DFL)

                        os.dup2(os.open(os.devnull, os.O_RDONLY), 0)

                        if delay:
                            time.sleep(delay)

                        os.chdir(self._config['wcDir'])

                        svc['toolImpl'].onRun(self._config, svc, [])
                    except Exception as e:
                        self._warn(str(e))
                        import traceback
                        self._warn(str(traceback.format_exc()))
                    finally:
                        sys.stdout.flush()
                        sys.stderr.flush()
                        # Should not be reachable here
                        os._exit(2)

            # Wait for children to exit
            try:
                self._interruptable = True

                if self._reload_services:
                    continue

                if not self._running:
                    break

                (pid, excode) = os.wait()
            except KeyboardInterrupt:
                continue
            except OSError as e:  # macOS
                self._warn(str(e))
                continue
            finally:
                self._interruptable = False

            svc = pid_to_svc[pid]
            del pid_to_svc[pid]
            svc['_pid'] = None
            svc['_lastExit2'] = svc['_lastExit1']

            try:
                svc['_lastExit1'] = time.monotonic()
            except:
                times = os.times()
                svc['_lastExit1'] = times[4]

            self._warn('Exited "{0}:{1}" pid "{2}" exit code "{3}"'.format(
                svc['name'], svc['instanceId'], pid, excode))

        # try terminate children
        # ---
        self._info('Terminating children')

        for svc in svc_list:
            pid = svc['_pid']

            if pid:
                try:
                    self._info('Terminating "{0}:{1}" pid "{2}"'.format(
                        svc['name'], svc['instanceId'], pid))
                    os.kill(pid, signal.SIGTERM)
                except OSError:
                    del pid_to_svc[pid]
                    self._info('Exited "{0}:{1}" pid "{2}"'.format(
                        svc['name'], svc['instanceId'], pid))

        # try wait children
        # ---
        self._info('Waiting for children')
        signal.signal(signal.SIGALRM, TimeoutException.alarmHandler)

        try:
            signal.setitimer(signal.ITIMER_REAL,
                             RuntimeTool.DEFAULT_EXIT_TIMEOUT / 1000.0)

            while len(pid_to_svc) > 0:
                (pid, excode) = os.waitpid(-1, 0)
                svc = pid_to_svc[pid]
                del pid_to_svc[pid]
                self._info('Exited "{0}:{1}" pid "{2}"'.format(
                    svc['name'], svc['instanceId'], pid))
        except TimeoutException:
            self._warn('Timed out waiting for children shutdown')
        except OSError as e:  # macOS
            self._warn(str(e))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

        # final kill
        # ---
        if pid_to_svc:
            self._info('Killing children')
        for pid in pid_to_svc:
            try:
                svc = pid_to_svc[pid]
                self._info('Killing "{0}:{1}" pid "{2}"'.format(
                    svc['name'], svc['instanceId'], pid))
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
            except OSError as e:
                self._warn(str(e))

        self._info('Master process exit')
        self._masterUnlock()
        self._dumpResourceStats()

    def _reloadServiceMaster(self):
        pid = self._serviceMasterPID()

        if pid:
            self._os.kill(pid, self._ext.signal.SIGUSR1)

    def _dumpResourceStats(self):
        resource = self._ext.resource
        configutil = self._configutil

        stats = resource.getrusage(resource.RUSAGE_SELF)
        self._infoLabel('Max RSS: ', configutil.toMemory(
            stats.ru_maxrss * 1024))
        self._infoLabel('User Time: ', '{0}s'.format(stats.ru_utime))
        self._infoLabel('System Time: ', '{0}s'.format(stats.ru_stime))
