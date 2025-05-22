#!/bin/bash
METHOD=$1
if [ -z "$METHOD" ]; then
    echo "Usage: $0 <method>"
    exit 1
fi

# Set benchmark parameters as variables (like in ReFrame test)
LATENCY_SIZE=8192       # 8K bytes
BANDWIDTH_SIZE=1048576  # 1MB (1024*1024)
# NUM_WARMUP_ITERS=10
# NUM_ITERS=1000

# Set up log directory
LOG_DIR="$HOME/hpc-project/log"
SCRIPTS_DIR="$HOME/hpc-project/scripts"
mkdir -p "$LOG_DIR" 

module load tools/numactl/2.0.16-GCCcore-13.2.0 2>/dev/null || echo "Warning: numactl module not found"

echo "===== Hardware Detection ====="
echo "Detecting hardware topology..."
$SCRIPTS_DIR/2.Hardware-Detection.sh
echo "Generating binding scripts..."
$SCRIPTS_DIR/2.Hardware-Detection.sh --generate-scripts

# Verify binding scripts were generated
echo "Checking generated binding scripts:"
ls -la ./bind_*.sh || echo "Failed to generate binding scripts"
chmod 755 ./bind_*.sh 2>/dev/null || echo "No binding scripts to chmod"

# Create symlinks to the OSU benchmarks
if [ -z "$EBROOTOSUMINMICROMINBENCHMARKS" ]; then
    echo "source /tmp/osu_env_$METHOD.sh"
    cat /tmp/osu_env_$METHOD.sh
    source /tmp/osu_env_$METHOD.sh
fi

OSU_DIR="$EBROOTOSUMINMICROMINBENCHMARKS/libexec/osu-micro-benchmarks/mpi/one-sided"
LATENCY_FILE="$OSU_DIR/osu_get_latency"
BANDWIDTH_FILE="$OSU_DIR/osu_get_bw"

if [ ! -f "$LATENCY_FILE" ]; then
    echo "Error: osu_get_latency not found at $LATENCY_FILE"
    exit 1
fi
if [ ! -f "$BANDWIDTH_FILE" ]; then
    echo "Error: osu_get_bw not found at $BANDWIDTH_FILE"
    exit 1
fi

# Create log files for placement tests
PLACEMENT_LOG="$LOG_DIR/placement_tests.log"
rm -f "$PLACEMENT_LOG" "$CSV_LOG" 2>/dev/null || true

# Function to run test and log results - matching ReFrame approach
run_placement_test() {
    local benchmark="$1"
    local placement="$2"
    local slurm_options="$3"
    local size=$([ "$benchmark" == "get_latency" ] && echo $LATENCY_SIZE || echo $BANDWIDTH_SIZE)
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local value=""
    local unit=""
    local result=""
    
    echo "================================================="
    echo "[$timestamp] Running $benchmark with $placement placement" 
    echo "Slurm options: $slurm_options" 
    echo "Parameters: size=$size, warmup=$NUM_WARMUP_ITERS, iterations=$NUM_ITERS"
    echo "-------------------------------------------------"
    
    BENCHMARK_FILE=$LATENCY_FILE
    if [ "$benchmark" == "get_bw" ]; then
        BENCHMARK_FILE=$BANDWIDTH_FILE
    fi
    
    # Run benchmark and capture the output
    echo "Running: srun $slurm_options $BENCHMARK_FILE"
    srun $slurm_options $BENCHMARK_FILE | tee -a "$PLACEMENT_LOG"
    
    # Initialize variable for binding options
    tmp_str=""
    
    # Set appropriate binding options based on placement type
    if [ "$placement" == "diff_numa_same_socket" ]; then
        tmp_str="--cpu-bind=verbose,map_cpu:0,16"
    elif [ "$placement" == "diff_socket_same_node" ]; then
        # Determine CPU mapping based on system
        if hostname | grep -q aion; then
            tmp_str="--cpu-bind=verbose,map_cpu:0,64"
        else
            tmp_str="--cpu-bind=verbose,map_cpu:0,1"
        fi
    fi

    # Run verification if hw-detect.sh exists
    if [ -f "./hw-detect.sh" ]; then
        echo "Placement verification:"
        srun -n2 $tmp_str ./hw-detect.sh --verify | tee -a "$PLACEMENT_LOG"
    else
        echo "Skipping verification (hw-detect.sh not found)" | tee -a "$PLACEMENT_LOG"
    fi
    # Return the result for display
    echo "$value $unit"
}

# Main test execution with all placement types
echo "===== Starting Placement Tests =====" | tee -a "$PLACEMENT_LOG"
echo "Date: $(date)" | tee -a "$PLACEMENT_LOG"
echo "Test parameters: latency_size=$LATENCY_SIZE, bandwidth_size=$BANDWIDTH_SIZE" | tee -a "$PLACEMENT_LOG"
echo "                 warmup_iters=$NUM_WARMUP_ITERS, iters=$NUM_ITERS" | tee -a "$PLACEMENT_LOG"
echo "" | tee -a "$PLACEMENT_LOG"


# Same NUMA test
echo "Running same_numa test..." | tee -a "$PLACEMENT_LOG"
SAME_NUMA_OPTS="-N 1 -c 1 -n 2 --ntasks-per-socket 2"
run_placement_test "get_latency" "same_numa" "$SAME_NUMA_OPTS" | tee -a "$PLACEMENT_LOG"
run_placement_test "get_bw" "same_numa" "$SAME_NUMA_OPTS" | tee -a "$PLACEMENT_LOG"
# printf "%-25s | %-15s | %-15s\n" "same_numa" "$latency_result" "$bandwidth_result" | tee -a "$PLACEMENT_LOG"

# Different NUMA, same socket test
echo "Running diff_numa_same_socket test..." | tee -a "$PLACEMENT_LOG"
DIFF_NUMA_OPTS="-N1 -n2 -c1 --distribution=cyclic"
run_placement_test "get_latency" "diff_numa_same_socket" "$DIFF_NUMA_OPTS" | tee -a "$PLACEMENT_LOG"
run_placement_test "get_bw" "diff_numa_same_socket""$DIFF_NUMA_OPTS" | tee -a "$PLACEMENT_LOG"
# printf "%-25s | %-15s | %-15s\n" "diff_numa_same_socket" "$latency_result" "$bandwidth_result" | tee -a "$PLACEMENT_LOG"

# Different socket, same node test
echo "Running diff_socket_same_node test..." | tee -a "$PLACEMENT_LOG"
DIFF_SOCKET_OPTS="-N1 -n2 --ntasks-per-socket 1"
run_placement_test "get_latency" "diff_socket_same_node" "$DIFF_SOCKET_OPTS" | tee -a "$PLACEMENT_LOG"
run_placement_test "get_bw" "diff_socket_same_node" "$DIFF_SOCKET_OPTS" | tee -a "$PLACEMENT_LOG"
# printf "%-25s | %-15s | %-15s\n" "diff_socket_same_node" "$latency_result" "$bandwidth_result" | tee -a "$PLACEMENT_LOG"

# Different node testd
echo "Running diff_node test..." | tee -a "$PLACEMENT_LOG"
DIFF_NODE_OPTS="srun -N 2 -n 2 -c 1 --distribution=cyclic"
run_placement_test "get_latency" "diff_node" "$DIFF_NODE_OPTS" | tee -a "$PLACEMENT_LOG"
run_placement_test "get_bw" "diff_node" "$DIFF_NODE_OPTS" | tee -a "$PLACEMENT_LOG"
# printf "%-25s | %-15s | %-15s\n" "diff_node" "$latency_result" "$bandwidth_result" | tee -a "$PLACEMENT_LOG"


echo "" | tee -a "$PLACEMENT_LOG"
echo "✅ All placement tests completed." | tee -a "$PLACEMENT_LOG"
echo "Log file: $PLACEMENT_LOG" | tee -a "$PLACEMENT_LOG"
echo "To view results: less $PLACEMENT_LOG"
