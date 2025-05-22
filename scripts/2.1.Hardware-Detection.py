import os
import re
import subprocess
import json
from pathlib import Path
import shutil

def run_cmd(cmd):
    """Run a shell command and return its output"""
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout.strip()

def detect_hardware_topology(scripts_dir=None):
    """Detect hardware topology within Slurm allocation"""
    if scripts_dir is None:
        scripts_dir = os.getcwd()
        
    print("===== Hardware Topology Detection =====")
    
    # Basic hardware detection
    numa_count = run_cmd("lscpu | grep '^NUMA node(s):' | awk '{print $3}'")
    socket_count = run_cmd("lscpu | grep '^Socket(s):' | awk '{print $2}'")
    
    print(f"Detected configuration:")
    print(f"- {numa_count} NUMA node(s)")
    print(f"- {socket_count} socket(s)")
    
    # Get CPUs allocated to this job by Slurm
    slurm_job_id = os.environ.get('SLURM_JOB_ID')
    if slurm_job_id:
        print(f"Running under Slurm job {slurm_job_id}")
        allocated_cpus = run_cmd("grep Cpus_allowed_list /proc/self/status | awk '{print $2}'")
        print(f"CPUs allocated to this job: {allocated_cpus}")
    else:
        print("Not running under Slurm - using all CPUs")
        total_cpus = int(run_cmd("nproc"))
        allocated_cpus = ",".join(str(i) for i in range(total_cpus))
    
    # Build socket->NUMA node map using allocated CPUs
    socket_numa_map = {}  # socket -> list of NUMA nodes
    numa_cpus_map = {}    # NUMA node -> list of CPUs
    
    # Process each CPU and build the hierarchy
    cpu_ranges = allocated_cpus.split(',')
    for cpu_range in cpu_ranges:
        if '-' in cpu_range:
            # Handle range like 0-127
            start, end = map(int, cpu_range.split('-'))
            cpu_list = range(start, end + 1)
        else:
            # Handle single CPU
            cpu_list = [int(cpu_range)]
        
        for cpu in cpu_list:
            # Get NUMA node and socket for this CPU
            node_cmd = f"lscpu -p=cpu,node | grep '^{cpu},' | cut -d, -f2"
            socket_cmd = f"lscpu -p=cpu,socket | grep '^{cpu},' | cut -d, -f2"
            
            node = run_cmd(node_cmd)
            socket = run_cmd(socket_cmd)
            
            # Skip if we couldn't determine the node or socket
            if not node or not socket:
                continue
                
            # Build the maps
            if socket not in socket_numa_map:
                socket_numa_map[socket] = [node]
            elif node not in socket_numa_map[socket]:
                socket_numa_map[socket].append(node)
            
            if node not in numa_cpus_map:
                numa_cpus_map[node] = [cpu]
            else:
                numa_cpus_map[node].append(cpu)
    
    # Print discovered topology
    print("Socket -> NUMA node mapping:")
    for socket, nodes in socket_numa_map.items():
        print(f"- Socket {socket}: NUMA nodes {' '.join(nodes)}")
    
    print("NUMA node -> CPUs mapping:")
    for node, cpus in numa_cpus_map.items():
        print(f"- NUMA node {node}: CPUs {' '.join(map(str, cpus))}")
    
    # Select nodes for different placement scenarios
    # Default to first socket's first NUMA node
    socket_list = list(socket_numa_map.keys())
    first_socket = socket_list[0] if socket_list else '0'
    first_socket_numas = socket_numa_map.get(first_socket, ['0'])
    numa_same = first_socket_numas[0]
    
    # For same-socket, different NUMA scenario
    if len(first_socket_numas) > 1:
        numa_diff_same_socket_1 = first_socket_numas[0]
        numa_diff_same_socket_2 = first_socket_numas[1]
    else:
        numa_diff_same_socket_1 = first_socket_numas[0]
        numa_diff_same_socket_2 = first_socket_numas[0]
        print(f"Warning: Only one NUMA node in socket {first_socket}, using same NUMA for same-socket test")
    
    # For different-socket scenario
    if len(socket_list) > 1:
        second_socket = socket_list[1]
        second_socket_numas = socket_numa_map.get(second_socket, ['0'])
        numa_diff_socket_1 = first_socket_numas[0]
        numa_diff_socket_2 = second_socket_numas[0]
    else:
        numa_diff_socket_1 = first_socket_numas[0]
        numa_diff_socket_2 = first_socket_numas[0]
        print("Warning: Only one socket available, using same socket for different-socket test")
    
    # Create JSON file with our mapping for Python
    topology_data = {
        "numa_count": numa_count,
        "socket_count": socket_count,
        "numa_same": numa_same,
        "numa_diff_same_socket_1": numa_diff_same_socket_1,
        "numa_diff_same_socket_2": numa_diff_same_socket_2,
        "numa_diff_socket_1": numa_diff_socket_1,
        "numa_diff_socket_2": numa_diff_socket_2,
        "socket_numa_map": socket_numa_map,
        "numa_cpus_map": {node: [str(cpu) for cpu in cpus] for node, cpus in numa_cpus_map.items()}
    }
    
    with open(f"{scripts_dir}/binding_vars.json", "w") as f:
        json.dump(topology_data, f, indent=2)
    
    # Also create bash binding variables for compatibility
    with open(f"{scripts_dir}/binding_vars.sh", "w") as f:
        f.write("#!/bin/bash\n")
        f.write(f"export NUMA_COUNT={numa_count}\n")
        f.write(f"export SOCKET_COUNT={socket_count}\n")
        f.write(f"export NUMA_SAME={numa_same}\n")
        f.write(f"export NUMA_DIFF_SAME_SOCKET_1={numa_diff_same_socket_1}\n")
        f.write(f"export NUMA_DIFF_SAME_SOCKET_2={numa_diff_same_socket_2}\n")
        f.write(f"export NUMA_DIFF_SOCKET_1={numa_diff_socket_1}\n")
        f.write(f"export NUMA_DIFF_SOCKET_2={numa_diff_socket_2}\n\n")
        
        # Socket to NUMA node mapping
        f.write("# Socket to NUMA node mapping\n")
        f.write("declare -A SOCKET_NUMA_MAP\n")
        for socket, nodes in socket_numa_map.items():
            f.write(f"SOCKET_NUMA_MAP[{socket}]=\"{' '.join(nodes)}\"\n")
        
        # NUMA to CPU mapping
        f.write("\n# NUMA node to CPU mapping\n")
        f.write("declare -A NUMA_CPUS_MAP\n")
        for node, cpus in numa_cpus_map.items():
            f.write(f"NUMA_CPUS_MAP[{node}]=\"{' '.join(map(str, cpus))}\"\n")
    
    os.chmod(f"{scripts_dir}/binding_vars.sh", 0o755)
    print(f"Hardware topology detected and saved to {scripts_dir}/binding_vars.json and {scripts_dir}/binding_vars.sh")
    
    return topology_data

def generate_placement_scripts(scripts_dir=None, topology_data=None):
    """Generate helper scripts for different process placement scenarios"""
    if scripts_dir is None:
        scripts_dir = os.getcwd()
    
    print("Generating placement helper scripts...")
    
    # If topology data not provided, check if we have a saved file or run detection
    if topology_data is None:
        json_path = f"{scripts_dir}/binding_vars.json"
        if os.path.exists(json_path):
            with open(json_path) as f:
                topology_data = json.load(f)
        else:
            topology_data = detect_hardware_topology(scripts_dir)
    
    # Also generate the shell scripts for compatibility
    with open(f"{scripts_dir}/bind_same_numa.sh", "w") as f:
        f.write("""#!/bin/bash
            # Bind both processes to the same NUMA node
            source $(dirname $0)/binding_vars.sh

            # Use the same NUMA for both processes
            BINDING_NODE=$NUMA_SAME

            echo "Case same NUMA; Binding all processes to NUMA node $BINDING_NODE"
            numactl --cpunodebind=$BINDING_NODE "$@"
        """)

    with open(f"{scripts_dir}/bind_diff_numa_same_socket.sh", "w") as f:
        f.write("""#!/bin/bash
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
        """)

    with open(f"{scripts_dir}/bind_diff_socket.sh", "w") as f:
        f.write("""#!/bin/bash
            # Bind processes to different sockets
            source $(dirname $0)/binding_vars.sh

            # Apply binding based on task ID
            if [ "$SLURM_PROCID" = "0" ]; then
                echo "Case different socket; Task 0: Binding to NUMA node $NUMA_DIFF_SOCKET_1"
                numactl --cpunodebind=$NUMA_DIFF_SOCKET_1 "$@"
            else
                echo "Case different socket; Task 1: Binding to NUMA node $NUMA_DIFF_SOCKET_2"
                numactl --cpunodebind=$NUMA_DIFF_SOCKET_2 "$@"
            fi
        """)

    # Make all scripts executable
    for script in ["bind_same_numa.sh", "bind_diff_numa_same_socket.sh", "bind_diff_socket.sh"]:
        os.chmod(f"{scripts_dir}/{script}", 0o755)
    
    print(f"Helper scripts generated in {scripts_dir}:")
    print("- Shell scripts: bind_same_numa.sh, bind_diff_numa_same_socket.sh, bind_diff_socket.sh")

def main():
    """Main function"""
    scripts_dir = os.getcwd()
    
    # Parse command-line arguments
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "--generate-scripts":
            generate_placement_scripts(scripts_dir)
        else:
            # Default behavior: just detect topology
            detect_hardware_topology(scripts_dir)
    else:
        # Default behavior: just detect topology
        detect_hardware_topology(scripts_dir)

if __name__ == "__main__":
    import sys
    main()