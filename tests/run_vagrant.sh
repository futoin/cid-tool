#!/bin/bash

vm=$1
shift 1

if [ -z "$vm" ]; then
    echo "Usage: $(basename $0) <vm>"
    exit 1
fi

echo "Running up $vm"
vagrant up $vm >/dev/null
vagrant rsync $vm #>/dev/null
vagrant ssh $vm -c "cd /vagrant && tests/run.sh $*"
vagrant ssh $vm -- cat /testrun/stdout.log > tests/logs/${vm}.log
res=$?
#vagrant 
exit $res
