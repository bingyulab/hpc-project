#!/bin/bash

# Setup environment
LOG_DIR="$HOME/hpc-project/log"
SCRIPTS_DIR="$PWD"
mkdir -p "$LOG_DIR" "$SCRIPTS_DIR"

# Function to detect hardware topology within Slurm allocation
detect_hardware_topology() {
    echo "===== Hardware Topology Detection ====="
    
    # Basic hardware detection
    NUMA_COUNT=$(lscpu | grep "^NUMA node(s):" | awk '{print $3}')
    SOCKET_COUNT=$(lscpu | grep "^Socket(s):" | awk '{print $2}')
    
    echo "Detected configuration:"
    echo "- $NUMA_COUNT NUMA node(s)"
    echo "- $SOCKET_COUNT socket(s)"
    
    # Get CPUs allocated to this job by Slurm
    if [ -n "$SLURM_JOB_ID" ]; then
        echo "Running under Slurm job $SLURM_JOB_ID"
        ALLOCATED_CPUS=$(grep Cpus_allowed_list /proc/self/status | awk '{print $2}')
        echo "CPUs allocated to this job: $ALLOCATED_CPUS"
    else
        echo "Not running under Slurm - using all CPUs"
        ALLOCATED_CPUS=$(seq -s, 0 $(($(nproc)-1)))
    fi
    
    # Build socket->NUMA node map using allocated CPUs
    declare -A SOCKET_NUMA_MAP
    declare -A NUMA_CPUS_MAP
    
    # Process each CPU and build the hierarchy
    IFS=',' read -ra CPU_RANGES <<< "$ALLOCATED_CPUS"
    for range in "${CPU_RANGES[@]}"; do
        if [[ $range == *-* ]]; then
            # Handle range like 0-127
            start="${range%-*}"
            end="${range#*-}"
            for ((cpu=start; cpu<=end; cpu++)); do
                # Get NUMA node and socket for this CPU
                node=$(lscpu -p=cpu,node | grep "^$cpu," | cut -d, -f2)
                socket=$(lscpu -p=cpu,socket | grep "^$cpu," | cut -d, -f2)
                
                # Skip if we couldn't determine the node or socket
                [ -z "$node" ] || [ -z "$socket" ] && continue
                
                # Build the maps
                if [ -z "${SOCKET_NUMA_MAP[$socket]}" ]; then
                    SOCKET_NUMA_MAP[$socket]="$node"
                elif [[ ! " ${SOCKET_NUMA_MAP[$socket]} " =~ " $node " ]]; then
                    SOCKET_NUMA_MAP[$socket]="${SOCKET_NUMA_MAP[$socket]} $node"
                fi
                
                if [ -z "${NUMA_CPUS_MAP[$node]}" ]; then
                    NUMA_CPUS_MAP[$node]="$cpu"
                else
                    NUMA_CPUS_MAP[$node]="${NUMA_CPUS_MAP[$node]} $cpu"
                fi
            done
        else
            # Handle single CPU
            cpu=$range
            node=$(lscpu -p=cpu,node | grep "^$cpu," | cut -d, -f2)
            socket=$(lscpu -p=cpu,socket | grep "^$cpu," | cut -d, -f2)
            
            # Skip if we couldn't determine the node or socket
            [ -z "$node" ] || [ -z "$socket" ] && continue
            
            # Build the maps
            if [ -z "${SOCKET_NUMA_MAP[$socket]}" ]; then
                SOCKET_NUMA_MAP[$socket]="$node"
            elif [[ ! " ${SOCKET_NUMA_MAP[$socket]} " =~ " $node " ]]; then
                SOCKET_NUMA_MAP[$socket]="${SOCKET_NUMA_MAP[$socket]} $node"
            fi
            
            if [ -z "${NUMA_CPUS_MAP[$node]}" ]; then
                NUMA_CPUS_MAP[$node]="$cpu"
            else
                NUMA_CPUS_MAP[$node]="${NUMA_CPUS_MAP[$node]} $cpu"
            fi
        fi
    done
    
    # Print discovered topology
    echo "Socket -> NUMA node mapping:"
    for socket in "${!SOCKET_NUMA_MAP[@]}"; do
        echo "- Socket $socket: NUMA nodes ${SOCKET_NUMA_MAP[$socket]}"
    done
    
    echo "NUMA node -> CPUs mapping:"
    for node in "${!NUMA_CPUS_MAP[@]}"; do
        echo "- NUMA node $node: CPUs ${NUMA_CPUS_MAP[$node]}"
    done
    
    # Select nodes for different placement scenarios
    # Default to first socket's first NUMA node
    SOCKET_LIST=(${!SOCKET_NUMA_MAP[@]})
    FIRST_SOCKET=${SOCKET_LIST[0]:-0}
    FIRST_SOCKET_NUMAS=(${SOCKET_NUMA_MAP[$FIRST_SOCKET]})
    NUMA_SAME=${FIRST_SOCKET_NUMAS[0]:-0}
    
    # For same-socket, different NUMA scenario
    if [ ${#FIRST_SOCKET_NUMAS[@]} -gt 1 ]; then
        NUMA_DIFF_SAME_SOCKET_1=${FIRST_SOCKET_NUMAS[0]}
        NUMA_DIFF_SAME_SOCKET_2=${FIRST_SOCKET_NUMAS[1]}
    else
        NUMA_DIFF_SAME_SOCKET_1=${FIRST_SOCKET_NUMAS[0]:-0}
        NUMA_DIFF_SAME_SOCKET_2=${FIRST_SOCKET_NUMAS[0]:-0}
        echo "Warning: Only one NUMA node in socket $FIRST_SOCKET, using same NUMA for same-socket test"
    fi
    
    # For different-socket scenario
    if [ ${#SOCKET_LIST[@]} -gt 1 ]; then
        SECOND_SOCKET=${SOCKET_LIST[1]}
        SECOND_SOCKET_NUMAS=(${SOCKET_NUMA_MAP[$SECOND_SOCKET]})
        NUMA_DIFF_SOCKET_1=${FIRST_SOCKET_NUMAS[0]:-0}
        NUMA_DIFF_SOCKET_2=${SECOND_SOCKET_NUMAS[0]:-0}
    else
        NUMA_DIFF_SOCKET_1=${FIRST_SOCKET_NUMAS[0]:-0}
        NUMA_DIFF_SOCKET_2=${FIRST_SOCKET_NUMAS[0]:-0}
        echo "Warning: Only one socket available, using same socket for different-socket test"
    fi
    
    # Create binding variables file with our mapping
    cat > $SCRIPTS_DIR/binding_vars.sh << EOF
#!/bin/bash
export NUMA_COUNT=$NUMA_COUNT
export SOCKET_COUNT=$SOCKET_COUNT
export NUMA_SAME=$NUMA_SAME
export NUMA_DIFF_SAME_SOCKET_1=$NUMA_DIFF_SAME_SOCKET_1
export NUMA_DIFF_SAME_SOCKET_2=$NUMA_DIFF_SAME_SOCKET_2
export NUMA_DIFF_SOCKET_1=$NUMA_DIFF_SOCKET_1
export NUMA_DIFF_SOCKET_2=$NUMA_DIFF_SOCKET_2

# Socket to NUMA node mapping
declare -A SOCKET_NUMA_MAP
EOF

    # Add the socket mapping
    for socket in "${!SOCKET_NUMA_MAP[@]}"; do
        echo "SOCKET_NUMA_MAP[$socket]=\"${SOCKET_NUMA_MAP[$socket]}\"" >> $SCRIPTS_DIR/binding_vars.sh
    done
    
    # Add the NUMA to CPU mapping
    echo -e "\n# NUMA node to CPU mapping\ndeclare -A NUMA_CPUS_MAP" >> $SCRIPTS_DIR/binding_vars.sh
    for node in "${!NUMA_CPUS_MAP[@]}"; do
        echo "NUMA_CPUS_MAP[$node]=\"${NUMA_CPUS_MAP[$node]}\"" >> $SCRIPTS_DIR/binding_vars.sh
    done
    
    chmod +x $SCRIPTS_DIR/binding_vars.sh
    echo "Hardware topology detected and saved to $SCRIPTS_DIR/binding_vars.sh"
}

# Generate placement helper scripts
generate_placement_scripts() {
    echo "Generating placement helper scripts..."
    
    # First, get the topology info from the detect function if not already done
    if [ ! -f "$SCRIPTS_DIR/binding_vars.sh" ]; then
        detect_hardware_topology
    fi
    
    # Source the binding variables
    source $SCRIPTS_DIR/binding_vars.sh
    
    # Script for binding to the same NUMA node
    cat > $SCRIPTS_DIR/bind_same_numa.sh << EOF
#!/bin/bash
# Bind both processes to the same NUMA node
source \$(dirname \$0)/binding_vars.sh

# Use the same NUMA for both processes
BINDING_NODE=\$NUMA_SAME

echo "Binding all processes to NUMA node \$BINDING_NODE"
numactl --cpunodebind=\$BINDING_NODE --membind=\$BINDING_NODE "\$@"
EOF
    chmod +x $SCRIPTS_DIR/bind_same_numa.sh

    # Script for binding to different NUMA nodes on same socket
    cat > $SCRIPTS_DIR/bind_diff_numa_same_socket.sh << EOF
#!/bin/bash
# Bind processes to different NUMA nodes on the same socket
source \$(dirname \$0)/binding_vars.sh

# Apply binding based on task ID
if [ "\$SLURM_PROCID" = "0" ]; then
    echo "Task 0: Binding to NUMA node \$NUMA_DIFF_SAME_SOCKET_1"
    numactl --cpunodebind=\$NUMA_DIFF_SAME_SOCKET_1 --membind=\$NUMA_DIFF_SAME_SOCKET_1 "\$@"
else
    echo "Task 1: Binding to NUMA node \$NUMA_DIFF_SAME_SOCKET_2"
    numactl --cpunodebind=\$NUMA_DIFF_SAME_SOCKET_2 --membind=\$NUMA_DIFF_SAME_SOCKET_2 "\$@"
fi
EOF
    chmod +x $SCRIPTS_DIR/bind_diff_numa_same_socket.sh

    # Script for binding to different sockets
    cat > $SCRIPTS_DIR/bind_diff_socket.sh << EOF
#!/bin/bash
# Bind processes to different sockets
source \$(dirname \$0)/binding_vars.sh

# Apply binding based on task ID
if [ "\$SLURM_PROCID" = "0" ]; then
    echo "Task 0: Binding to NUMA node \$NUMA_DIFF_SOCKET_1"
    numactl --cpunodebind=\$NUMA_DIFF_SOCKET_1 --membind=\$NUMA_DIFF_SOCKET_1 "\$@"
else
    echo "Task 1: Binding to NUMA node \$NUMA_DIFF_SOCKET_2"
    numactl --cpunodebind=\$NUMA_DIFF_SOCKET_2 --membind=\$NUMA_DIFF_SOCKET_2 "\$@"
fi
EOF
    chmod +x $SCRIPTS_DIR/bind_diff_socket.sh
    
    # Verify the scripts were created
    ls -l $SCRIPTS_DIR/bind_*.sh
    
    echo "Helper scripts generated in $SCRIPTS_DIR:"
    echo "- bind_same_numa.sh: Bind tasks to the same NUMA node"
    echo "- bind_diff_numa_same_socket.sh: Bind tasks to different NUMA nodes on same socket"
    echo "- bind_diff_socket.sh: Bind tasks to different sockets"
}

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
            generate_placement_scripts
            return 0
            ;;
        --verify)
            verify_placement
            return 0
            ;;
        *)
            # Default behavior: just detect topology
            detect_hardware_topology
            return 0
            ;;
    esac
}

# Run main function with command line arguments
main "$@"