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


from ..mixins.log import LogMixIn
from ..mixins.ondemand import OnDemandMixIn

from collections import OrderedDict


class ResourceAlgo(LogMixIn, OnDemandMixIn):
    CID_MIN_MEMORY = '48M'

    def pageSize(self):
        return self._os.sysconf('SC_PAGE_SIZE')

    def systemMemory(self):
        try:
            return self.pageSize() * self._os.sysconf('SC_PHYS_PAGES')
        except ValueError:
            if self._detect.isMacOS():
                return int(self._ext.subprocess.check_output(['sysctl', '-n', 'hw.memsize']).strip())
            else:
                self._errorExit('Failed to detect system memory size')

    def cgroupMemory(self, cgroupFile=None):
        cgroupFile = cgroupFile or '/sys/fs/cgroup/memory/memory.limit_in_bytes'

        if self._ospath.exists(cgroupFile):
            return int(self._pathutil.readTextFile(cgroupFile).strip())

        return None

    def memoryLimit(self, config):
        maxTotalMemory = config.get('deploy', {}).get('maxTotalMemory', None)

        if maxTotalMemory:
            return self._configutil.parseMemory(maxTotalMemory)

        sysMem = self.systemMemory()
        cgroupMem = self.cgroupMemory()

        if cgroupMem and cgroupMem < sysMem:
            return cgroupMem
        else:
            return sysMem / 2

    def systemCpuCount(self):
        if self._detect.isMacOS():
            return int(self._ext.subprocess.check_output(['sysctl', '-n', 'hw.ncpu']).strip())

        os = self._os
        return min(os.sysconf('SC_NPROCESSORS_ONLN'), os.sysconf('SC_NPROCESSORS_CONF'))

    def cgroupCpuCount(self, cgroupFile=None):
        cgroupFile = cgroupFile or '/sys/fs/cgroup/cpuset/cpuset.cpus'

        if not self._ospath.exists(cgroupFile):
            return None

        cpus = self._pathutil.readTextFile(cgroupFile).strip()
        cpus = cpus.split(',')
        count = 0

        for c in cpus:
            c = c.split('-')

            if len(c) == 2:
                count += len(range(int(c[0]), int(c[1]) + 1))
            else:
                count += 1

        return count

    def cpuLimit(self, config):
        maxCpuCount = config.get('deploy', {}).get('maxCpuCount', None)

        if maxCpuCount:
            return maxCpuCount

        cpu_count = self.systemCpuCount()
        cgroup_count = self.cgroupCpuCount()

        if cgroup_count:
            return min(cpu_count, cgroup_count)
        else:
            return cpu_count

    def configServices(self, config):
        memLimit = self.memoryLimit(config)
        cpuLimit = self.cpuLimit(config)

        self.distributeResources(config, memLimit, cpuLimit)
        self.assignSockets(config)

    def distributeResources(self, config, maxmem, maxcpu, granularity=None):
        import math
        configutil = self._configutil

        if granularity is None:
            granularity = self.pageSize()

        maxmem = maxmem // granularity
        availMem = maxmem
        deploy = config.setdefault('deploy', {})
        autoServices = deploy.setdefault('autoServices', {})
        entryPoints = config.get('entryPoints', {})

        services = {}
        candidates = set()
        env = config.get('env', {})
        debug = (env.get('type', 'dev') == 'dev')
        external_services = env.get('externalServices', [])
        cid_min_memory = configutil.parseMemory(
            self.CID_MIN_MEMORY) // granularity

        # Init
        for (en, ei) in entryPoints.items():
            tool = ei['tool']
            ei = ei.get('tune', {}).copy()

            for f in ('minMemory', 'connMemory', 'maxRequestSize'):
                if f not in ei:
                    self._errorExit(
                        '"{0}" is missing from {1} entry point'.format(f, en))
                ei[f] = configutil.parseMemory(ei[f]) // granularity

            for f in ('maxMemory', 'maxTotalMemory', 'debugOverhead', 'debugConnOverhead'):
                if f in ei:
                    ei[f] = configutil.parseMemory(ei[f]) // granularity

            for f in ('socketProtocol',):
                if f not in ei:
                    self._errorExit(
                        '"{0}" is missing from {1} entry point'.format(f, en))

            ei.setdefault('connFD', 16)
            ei.setdefault('memWeight', 100)
            ei.setdefault('cpuWeight', 100)
            ei.setdefault('maxMemory', maxmem)
            ei.setdefault('maxTotalMemory', maxmem)
            ei.setdefault('scalable', True)
            ei.setdefault('multiCore', True)
            ei.setdefault('reloadable', False)

            if debug:
                ei['minMemory'] += ei.get('debugOverhead', 0)
                ei['connMemory'] += ei.get('debugConnOverhead', 0)

            if (not ei['scalable']) and ei['maxMemory'] < ei['maxTotalMemory']:
                ei['maxTotalMemory'] = ei['maxMemory']

            ei['instances'] = 1
            ei['memAlloc'] = max(
                ei['minMemory'] + ei['connMemory'], cid_min_memory)

            disabled = tool in external_services
            ei['disabled'] = disabled

            if not disabled:
                availMem -= ei['memAlloc']
                candidates.add(en)

            services[en] = ei

        if availMem < 0:
            self._errorExit(
                'Not enough memory to allocate services: deficit "{0}" bytes'.format(availMem))

        # Distribute remaining
        while availMem > 0 and len(candidates) > 0:
            overall_weight = 0

            for en in candidates:
                overall_weight += services[en]['memWeight']

            distMem = availMem
            to_del = set()

            for en in candidates:
                ei = services[en]
                memAlloc = ei['memAlloc']
                addAlloc = distMem * ei['memWeight'] // overall_weight

                if (memAlloc + addAlloc) > ei['maxTotalMemory']:
                    ei['memAlloc'] = ei['maxTotalMemory']
                    addAlloc = ei['memAlloc'] - memAlloc
                    to_del.add(en)
                else:
                    ei['memAlloc'] += addAlloc

                availMem -= addAlloc

            candidates -= to_del

            if availMem == distMem:
                break

        # Distribute instances
        min_mem_coeff = 2

        for (en, ei) in services.items():
            if ei['disabled']:
                ei['maxCpuCount'] = '1'
                continue

            if not ei['scalable']:
                ei['maxCpuCount'] = maxcpu
                continue

            reasonableMinMemory = ei['minMemory'] * min_mem_coeff
            reasonableMinMemory = max(reasonableMinMemory, cid_min_memory)

            if ei['multiCore']:
                if (not ei['reloadable']) and ei['memAlloc'] >= (reasonableMinMemory * 2):
                    ei['instances'] = 2
                    ei['maxCpuCount'] = int(math.ceil(maxcpu / 2.0))
                else:
                    ei['maxCpuCount'] = maxcpu
            else:
                possible_instances = ei['memAlloc'] // reasonableMinMemory

                if possible_instances == 0 and ei['memAlloc'] > ei['minMemory']:
                    possible_instances = 1

                if ei['reloadable'] or maxcpu > 1:
                    ei['instances'] = min(maxcpu, possible_instances)
                else:
                    ei['instances'] = min(2, possible_instances)

                ei['maxCpuCount'] = 1

            ei['instances'] = min(ei['instances'], ei.get(
                'maxInstances', ei['instances']))

        # create services
        for (en, ei) in services.items():
            instances = []
            instance_count = ei['instances']
            service_mem = 0

            if instance_count <= 0:
                self._errorExit(
                    'Failed to allocate instances for "{0}"'.format(en))
            elif ei['disabled']:
                instance_count = 0

            for i in range(0, instance_count):
                ic = OrderedDict()
                instance_mem = ei['memAlloc'] // instance_count
                ic['maxMemory'] = instance_mem
                ic['connMemory'] = ei['connMemory']
                service_mem += instance_mem
                instances.append(ic)

            if instance_count > 0:
                instances[0]['maxMemory'] += (ei['memAlloc'] - service_mem)

            for ic in instances:
                ic['maxConnections'] = int(
                    ic['maxMemory'] - ei['minMemory']) // ei['connMemory']

                ic['maxFD'] = int(ei['connFD'] * ic['maxConnections'])
                ic['maxCpuCount'] = ei['maxCpuCount']
                ic['maxRequestSize'] = ei['maxRequestSize']
                ic['socketProtocol'] = ei['socketProtocol']

                for m in ('maxMemory', 'connMemory', 'maxRequestSize'):
                    ic[m] = configutil.toMemory(ic[m] * granularity)

            autoServices[en] = instances

    def assignSockets(self, config):
        port = 1025
        ports = set()
        deploy = config['deploy']
        autoServices = deploy['autoServices']
        entryPoints = config.get('entryPoints', {})

        ospath = self._ospath
        pathutil = self._pathutil
        os = self._os
        base_dir = ospath.realpath(config['deployDir'])
        run_dir = pathutil.safeJoin(base_dir, '.runtime')
        run_dir = deploy.setdefault('runtimeDir', run_dir)
        tmp_dir = pathutil.safeJoin(base_dir, '.tmp')
        tmp_dir = deploy.setdefault('tmpDir', tmp_dir)

        for (en, instances) in autoServices.items():
            ei = entryPoints[en].get('tune', {})

            if 'socketType' in ei and 'socketTypes' not in ei:
                self._errorExit(
                    'Entry point "{0}" sets socketType without socketTypes'.format(en))

            socket_types = ei.get('socketTypes', [])

            if not socket_types:
                continue

            sock_type = ei.get('socketType', socket_types[0])

            for i in range(0, len(instances)):
                ic = instances[i]

                ic['socketType'] = sock_type

                if sock_type == 'unix':
                    ic['socketPath'] = pathutil.safeJoin(
                        run_dir, '{0}.{1}.sock'.format(en, i))
                else:
                    if sock_type == 'tcp6':
                        def_addr = '::'
                    else:
                        def_addr = '0.0.0.0'

                    ic['socketAddress'] = deploy.get(
                        'listenAddress', def_addr)

                    if 'socketPort' in ei:
                        sock_port = int(ei['socketPort']) + i
                    else:
                        sock_port = port
                        port += 1

                    if sock_port in ports:
                        self._errorExit(
                            'Port "{0}" is already in use'.format(sock_port))

                    ic['socketPort'] = sock_port
                    ports.add(sock_port)
