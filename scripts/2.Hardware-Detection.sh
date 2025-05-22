#!/bin/bash

# Setup environment
LOG_DIR="$HOME/hpc-project/log"
SCRIPTS_DIR="$HOME/hpc-project/scripts"
mkdir -p "$LOG_DIR" "$SCRIPTS_DIR"

# Function to verify process placement for current process
verify_placement() {
    local task_id=${SLURM_PROCID:-0}
    echo "==== Task $task_id placement ===="
    echo "Running on host: $(hostname)"
    
    if command -v numactl >/dev/null 2>&1; then
        echo "NUMA binding: $(numactl --show 2>/dev/null | grep -E 'nodebind|membind')"
    else
        echo "NUMA binding: numactl not available"
    fi
    
    if command -v lscpu >/dev/null 2>&1; then
        CPUS=$(taskset -cp $$ 2>/dev/null | grep -o "[0-9,-]*$" || echo "Unknown")
        echo "CPUs: $CPUS"
        
        # Get first CPU in the mask for node detection
        FIRST_CPU=$(echo $CPUS | cut -d, -f1 | cut -d- -f1)
        
        SOCKET=$(lscpu -p=cpu,socket | grep "^$FIRST_CPU," | cut -d, -f2)
        echo "Socket: $SOCKET"
        
        NUMA=$(lscpu -p=cpu,node | grep "^$FIRST_CPU," | cut -d, -f2)
        echo "NUMA node: $NUMA"
        
        # Additional CPU info
        CORE=$(lscpu -p=cpu,core | grep "^$FIRST_CPU," | cut -d, -f2)
        echo "Core: $CORE"
    else
        echo "CPU mapping: lscpu not available"
    fi
    
    echo "============================"
}

# Main function
main() {
    # First argument is the command
    cmd="$1"
    
    # Remove first argument for clean processing
    shift
    
    case "$cmd" in
        --generate-scripts)
            module load devel/ReFrame/4.7.4-GCCcore-13.2.0
            python $SCRIPTS_DIR/2.1.Hardware-Detection.py --generate-scripts
            return 0
            ;;
        --verify)
            verify_placement
            return 0
            ;;
        *)
            # Default behavior: just detect topology
            module load devel/ReFrame/4.7.4-GCCcore-13.2.0
            python $SCRIPTS_DIR/2.1.Hardware-Detection.py 
            return 0
            ;;
    esac
}

# Run main function with command line arguments
main "$@"