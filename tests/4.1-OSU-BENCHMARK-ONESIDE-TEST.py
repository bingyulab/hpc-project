import os
import reframe as rfm
import reframe.utility.sanity as sn
from reframe.core.builtins import parameter
import csv
import datetime
from config import REFERENCE_VALUES, MODULE_CONFIGS


class OSUMicroBenchmarkBase(rfm.RunOnlyRegressionTest):
    """Base class for OSU Micro-Benchmark tests"""
    
    valid_systems = ['*']
    valid_prog_environs = ['*']
    
    num_warmup_iters = 10
    num_iters = 1000
    device_buffers = 'cpu'
    kind = 'one-sided'
    test_type = parameter([
        ('osu_get_latency', 'latency'),
        ('osu_get_bw', 'bandwidth')
    ])
    
    # Define message sizes
    latency_size = 8192     # 8K bytes
    bandwidth_size = 1048576  # 1MB
    
    time_limit = '10m'
    exclusive = True
    
    # Add parameter for binary source
    binary_source = parameter(['local', 'easybuild', 'eessi'])
    
    @run_before('setup')
    def setup_per_benchmark(self):
        """Setup benchmark-specific parameters"""
        self.benchmark, self.metric = self.test_type
        
        # Determine unit based on metric
        if self.metric == 'latency':
            self.test_size = self.latency_size
            self.unit = 'us'
        else:  # bandwidth
            self.test_size = self.bandwidth_size
            self.unit = 'MB/s'
            
        # Set up the performance variable with our custom function
        self.perf_variables = {
            self.metric: sn.make_performance_function(
                self._extract_metric(self.test_size), self.unit
            )
        } 
        
    @run_before('run')
    def load_modules(self):
        """Load necessary modules based on binary source"""
        self.modules = []  
        
        self.prerun_cmds.extend(MODULE_CONFIGS[self.binary_source])
                
    @run_before('run')    
    def set_executable(self):
        """Set executable path and options"""
        if self.binary_source == 'local':
            # Local path can be set directly
            osu_dir = os.path.expanduser('~/osu-micro-benchmarks-7.2/build')
            self.executable = os.path.join(
                osu_dir, 'libexec/osu-micro-benchmarks/mpi', 
                self.kind, self.benchmark)
        elif self.binary_source in ['easybuild', 'eessi']:
            # For module-loaded paths, use shell variables instead
            # This will be expanded at runtime after modules are loaded
            self.executable = "${EBROOTOSUMINMICROMINBENCHMARKS}/libexec/osu-micro-benchmarks/mpi/${KIND}/${BENCHMARK}"
            
            # Export variables needed in the shell
            self.prerun_cmds.extend([
                'export KIND="' + self.kind + '"',
                'export BENCHMARK="' + self.benchmark + '"',
                # Add a fallback path finder if the module variable isn't set
                'if [ -z "$EBROOTOSUMINMICROMINBENCHMARKS" ]; then',
                '  echo "Warning: EBROOTOSUMINMICROMINBENCHMARKS not set, trying to find it..."',
                '  OSU_PATH=$(find /opt -name "osu_get_latency" -type f -executable 2>/dev/null | head -1)',
                '  if [ -n "$OSU_PATH" ]; then',
                '    export EBROOTOSUMINMICROMINBENCHMARKS=$(dirname $(dirname $(dirname $(dirname $OSU_PATH))))',
                '    echo "Found at: $EBROOTOSUMINMICROMINBENCHMARKS"',
                '  else',
                '    echo "Could not find OSU Micro-Benchmarks"',
                '    exit 1',
                '  fi',
                'fi',
                'echo "Using OSU benchmarks from: $EBROOTOSUMINMICROMINBENCHMARKS"'
            ])
        else:
            self.skip_if(True, 'Unknown binary source')
            return
        
        # Set basic executable options
        self.executable_opts = [
            '-m', str(self.test_size),
            '-x', str(self.num_warmup_iters),
            '-i', str(self.num_iters)
        ]
        
        # Verify executable exists
        self.prerun_cmds.append(
            f'if [ ! -x "{self.executable}" ]; then '
            f'echo "Benchmark executable not found: {self.executable}"; exit 1; fi'
        )
    
    def _extract_metric(self, size):
        """Extract benchmark metric from stdout with specific size"""
        return sn.extractsingle(rf'^{size}\s+(\S+)',
                               self.stdout, 1, float)
    
    @sanity_function
    def assert_output(self):
        return sn.assert_found(r'# OSU MPI', self.stdout)
    
    def set_reference_values(self, is_multi_node=False):
        """Common method to set reference values based on configuration"""
        system = self.current_system.name
        partition = self.current_partition.name  

        # Create reference key with environment
        key = f"{system}:{partition}"
        self.reference = dict()
        
        if system in REFERENCE_VALUES:
            # Set metric-specific reference values
            if self.metric in REFERENCE_VALUES[system]:
                ref_key = self.placement_type if self.placement_type  in REFERENCE_VALUES[system][self.metric][self.binary_source] else 'default'
                self.reference = {
                    key: {
                        self.metric: REFERENCE_VALUES[system][self.metric][self.binary_source][ref_key]
                    }
                }
        # print(f"Reference {self.reference}")   

@rfm.simple_test
class OSUPlacementTest(OSUMicroBenchmarkBase):
    """Tests process placement using numactl mechanism"""
    
    placement_type = parameter([
        'same_numa',
        'diff_numa_same_socket', 
        'diff_socket_same_node', 
        'diff_node'
    ])

    @run_after('setup')
    def set_placement_references(self):
        """Set reference values based on placement type"""
        is_multi = (self.placement_type == 'diff_node')
        self.set_reference_values(is_multi_node=is_multi)
        self.tags.add(f"dist_{self.placement_type}")

    @run_before('run')
    def set_job_options_for_placement(self):
        """Configure Slurm distribution options for different placement strategies"""
                
        source_script = os.path.expanduser('~/hpc-project/scripts/2.Hardware-Detection.sh')    

        self.prerun_cmds.extend([
            '# Create private copies of hardware detection script in stage directory',
            f'cp {source_script} ./hw-detect.sh',
            'chmod 755 ./hw-detect.sh',
            'echo "====== Available NUMA nodes on this host ======"',
            'numactl -H | grep "^node" || echo "No NUMA information available"',
            'echo "Generating binding scripts in stage directory..."',
            './hw-detect.sh --generate-scripts',
            'echo "Verifying binding scripts were generated:"',
            'ls -la ./bind_*.sh || echo "Failed to generate binding scripts"',
            'chmod 755 ./bind_*.sh 2>/dev/null || echo "No binding scripts to chmod"'
        ])
        
        tmp_str = ''
        if self.placement_type == 'same_numa':            
            self.num_nodes           = 1               
            self.num_tasks_per_socket= 2          
            self.num_tasks_per_node  = 2      
            self.num_tasks           = 2
            self.num_cpus_per_task   = 1
            
            SRUN_OPTIONS = '-N 1 -c 1 -n 2 --ntasks-per-socket 2 \
                --distribution=block:block:block'
                
            self.job.launcher.options = [    
                SRUN_OPTIONS,           
                './bind_same_numa.sh'
            ]
            
        elif self.placement_type == 'diff_numa_same_socket':                       
            
            self.job.options = ['-N 1 -n 2 --exclusive']
            
            SRUN_OPTIONS = '-N1 -n2 -c1 --distribution=cyclic'
            
            self.job.launcher.options = [    
                SRUN_OPTIONS,           
                './bind_diff_numa_same_socket.sh'
            ]        
            
            tmp_str = '--cpu-bind=verbose,map_cpu:0,16'
    
        elif self.placement_type == 'diff_socket_same_node':          
            
            self.job.options = ['-N 1 -n 2 --exclusive']
                            
            SRUN_OPTIONS = '-N1 -n2 --ntasks-per-socket 1'
                                
            self.job.launcher.options = [    
                SRUN_OPTIONS,
                './bind_diff_socket.sh'
            ]

            tmp_str = f'--cpu-bind=verbose,map_cpu:0,{64 if self.current_system.name == "aion" else 1}'
            
        elif self.placement_type == 'diff_node':
            self.num_nodes           = 2
            self.num_tasks_per_node  = 1     
            self.num_tasks           = 2
            self.num_cpus_per_task   = 1
                        
            self.job.launcher.options = [
                '--distribution=cyclic',
            ]
             
        # Add detailed verification AFTER running benchmark
        self.postrun_cmds = [
            'echo "==== Detailed Process Placement Verification (after benchmark) ===="',
            f'srun -n2 {tmp_str} bash -c \'echo "TASK $SLURM_PROCID on $(hostname): CPU $(taskset -cp $$), NUMA node $(cat /proc/self/status | grep Mems_allowed_list | cut -f2), Socket $(lscpu -p=cpu,socket | grep "^$(taskset -cp $$ | grep -o "[0-9]*$")," | cut -d, -f2)"\'',
            'echo "==== Verifying process placement ===="',
            f'srun -n2 {tmp_str} ./hw-detect.sh --verify'
        ]