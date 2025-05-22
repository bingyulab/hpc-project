#!/bin/bash --login
#SBATCH --nodes=1
#SBATCH --exclusive


srun --nodes=1 --ntasks-per-node=2 --ntasks-per-socket=1 --cpu-bind=verbose,map_cpu:0,65 bash -c 'CPU=$(taskset -cp $$ | grep -o "[0-9]*$"); TOPOLOGY=$(lscpu -p=cpu,socket,node | grep "^$CPU,"); SOCKET=$(echo $TOPOLOGY | cut -d, -f2); NUMA=$(echo $TOPOLOGY | cut -d, -f3); echo "Task $SLURM_PROCID: CPU $CPU, Socket $SOCKET, NUMA node $NUMA"'