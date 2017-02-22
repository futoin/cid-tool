#!/bin/bash

VM_LIST=$(vagrant status --machine-readable | grep metadata | cut -d, -f2)

for vm in $VM_LIST; do
    $(dirname $0)/run_vagrant.sh $vm
done
