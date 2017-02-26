#!/bin/bash

vm=$1
shift 1

if [ -z "$vm" ]; then
    echo "Usage: $(basename $0) <vm>"
    exit 1
fi

vagrant up $vm >/dev/null
vagrant rsync $vm #>/dev/null
vagrant ssh $vm -c "cd /vagrant && tests/run.sh $@"
res=$?
#vagrant 
exit $res
