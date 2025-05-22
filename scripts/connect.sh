#!/bin/bash

# connect.sh - Script to allocate resources on an HPC cluster using SLURM
# Usage: ./connect.sh [options]

# Default parameters
PARTITION="batch"        # Partition/queue to submit the job to
QOS="normal"             # Quality of Service (priority level)
TIME="4:00:00"           # Maximum walltime in HH:MM:SS format
NODES=2                  # <n> Number of compute nodes to allocate
TASKS=2                  # Total number of tasks/processes to run
CPUS=2                   # Number of CPU cores per task
# SOCKETS=2                # Number of CPU sockets per node to use
# TASKS_PER_SOCKET=4       # <s> Number of tasks to allocate per socket
TASKS_PER_NODE=32        # Number of tasks per node
# relations between <s> and <n> must be aligned with the physical NUMA characteristics of the node.
# For instance on aion nodes, <n> = 8*<s>
# For instance on iris regular nodes, <n>=2*<s> when on iris bigmem nodes, <n>=4*<s>.
X11_FLAG=""              # X11 forwarding flag, empty by default
CONSTRAINT=""            # Node features/constraints for selection
EXCLUSIVE="--exclusive"  # By default, request exclusive node access

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --partition) PARTITION="$2"; shift 2 ;;      # Specify compute partition
        --qos) QOS="$2"; shift 2 ;;                  # Specify QoS level
        --time) TIME="$2"; shift 2 ;;                # Set job time limit
        --nodes) NODES="$2"; shift 2 ;;              # Set number of nodes
        --tasks) TASKS="$2"; shift 2 ;;              # Set total number of tasks
        --cpus) CPUS="$2"; shift 2 ;;                # Set CPUs per task
        # --sockets) SOCKETS="$2"; shift 2 ;;          # Set sockets per node
        --ntasks-per-node) TASKS_PER_NODE="$2"; shift 2 ;; # NUMA domains per socket
        # --ntasks-per-socket) TASKS_PER_SOCKET="$2"; shift 2 ;; # Tasks per socket
        --x11) X11_FLAG="--x11"; shift ;;            # Enable X11 forwarding
        --constraint) CONSTRAINT="$2"; shift 2 ;;    # Set node constraints
        --shared) EXCLUSIVE=""; shift ;;             # Disable exclusive node access
        *)
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
done

# Build constraint option
CONSTRAINT_OPT=""
if [ -n "$CONSTRAINT" ]; then
    CONSTRAINT_OPT="-C $CONSTRAINT"
fi

# Check if Iris system
if [[ $(hostname) == access1.iris* ]]; then
    # Iris system detected
    echo "Detected Iris system"
    
    TASKS_PER_NODE=14
fi

echo "Requesting job with NUMA/socket topology:"
echo "- Nodes: $NODES"
# echo "- Sockets per node: $SOCKETS"
echo "- Tasks: $TASKS"
# echo "- Tasks per socket: $TASKS_PER_SOCKET"
echo "- CPUs per task: $CPUS"

# Execute salloc with specified NUMA/socket topology
echo salloc -p "$PARTITION" --qos "$QOS" --time "$TIME"\
 -N "$NODES" -n "$TASKS" -c "$CPUS"\
 --ntasks-per-node "$TASKS_PER_NODE"\
 $X11_FLAG $CONSTRAINT_OPT $EXCLUSIVE

salloc -p "$PARTITION" --qos "$QOS" --time "$TIME"\
 -N "$NODES" -n "$TASKS" -c "$CPUS"\
 --ntasks-per-node "$TASKS_PER_NODE"\
 $X11_FLAG $CONSTRAINT_OPT $EXCLUSIVE