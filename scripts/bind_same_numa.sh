#!/bin/bash
            # Bind both processes to the same NUMA node
            source $(dirname $0)/binding_vars.sh

            # Use the same NUMA for both processes
            BINDING_NODE=$NUMA_SAME

            echo "Case same NUMA; Binding all processes to NUMA node $BINDING_NODE"
            numactl --cpunodebind=$BINDING_NODE "$@"
        