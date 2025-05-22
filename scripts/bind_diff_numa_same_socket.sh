#!/bin/bash
            # Bind processes to different NUMA nodes on the same socket
            source $(dirname $0)/binding_vars.sh

            # Apply binding based on task ID
            if [ "$SLURM_PROCID" = "0" ]; then
                echo "Case different NUMA same socket; Task 0: Binding to NUMA node $NUMA_DIFF_SAME_SOCKET_1"
                numactl --cpunodebind=$NUMA_DIFF_SAME_SOCKET_1 "$@"
            else
                echo "Case different NUMA same socket; Task 1: Binding to NUMA node $NUMA_DIFF_SAME_SOCKET_2"
                numactl --cpunodebind=$NUMA_DIFF_SAME_SOCKET_2 "$@"
            fi
        