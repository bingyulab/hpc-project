# 🔍 **Project Goal**

You're building a **performance testing suite** using **ReFrame** to **measure MPI communication** latency and bandwidth on the **ULHPC clusters (IRIS and Aion)**.

You'll use:

- **OSU Micro-Benchmarks (OMB)** — specifically:
	- `osu_latency`: to measure **latency** (communication delay)	
	- `osu_bw`: to measure **bandwidth** (communication speed)

The big idea: You want to catch any **unexpected performance drops** in the cluster over time (due to updates, hardware changes, etc.) using **regression tests**.

---

## Project Flow: What You're Supposed to Do

### Step 1. **Install OSU Micro-Benchmarks**
#### 🛠️ **Three Ways to Use OSU Benchmarks**

You must test performance using all three versions of the benchmarks:

1. **Locally Compiled**
	- Compile from source **inside ReFrame**
	- Use `toolchain/foss/2023b` toolchain
```bash
cd ~/project
export OSU_VERSION=7.2 # Just to abstract from the version to download 
wget https://mvapich.cse.ohio-state.edu/download/mvapich/osu-micro-benchmarks-${OSU_VERSION}.tar.gz
tar -zxvf osu-micro-benchmarks-${OSU_VERSION}.tar.gz 
cd osu-micro-benchmarks-${OSU_VERSION}

mkdir build # Prepare the specific building directory 
cd build 
echo $OSU_VERSION # Check that the variable is defined and with teh appropriate value # Load the appropriate module 
module load toolchain/foss/2023b # Configure the Foss MPI-based build for installation in the current directory 
../configure CC=mpicc CFLAGS=-I$(pwd)/../util --prefix=$(pwd) 
make && make install
```
2. **EasyBuild Compiled**
	- Load a pre-built EasyBuild module	
	```bash
	module purge
	module load tools/EasyBuild/5.0.0
	eb ~/.local/easybuild/software/EasyBuild/5.0.0/easybuild/easyconfigs/o/OSU-Micro-Benchmarks/OSU-Micro-Benchmarks-7.2-gompi-2023b.eb
	module load perf/OSU-Micro-Benchmarks/7.2-gompi-2023b
	```
	Use `module show perf/OSU-Micro-Benchmarks/7.5-gompi-2020b` to locate the path `~/.local/easybuild/software/OSU-Micro-Benchmarks/7.5-gompi-2020b/easybuild/`. Then copy `log` file and `eb` file to `omb`.
3. **Precompiled from EESSI**
	- Use the EESSI software stack
	```bash
	module purge
	module load EESSI
	module load OSU-Micro-Benchmarks/7.2-gompi-2023b
	```

Each test case should work with **each of these three binary sources**.

 **Verification**

```bash
cd libexec/osu-micro-benchmarks/mpi/one-sided/ 
srun -n 2 ./osu_get_latency 
srun -n 2 ./osu_get_bw
```


---

###  Step 2. **Use `hwloc`**

- Visualize topology (`lstopo`)
```bash
module load system/hwloc
lstopo
```

On `Aion`:
```text
0 [bjiang@aion-0105 ~](7063811 1N/32T/32CN)$ hostname
aion-0105
0 [bjiang@aion-0105 ~](7063811 1N/32T/32CN)$ lstopo
Machine (251GB total)
  Package L#0
    Group0 L#0
      NUMANode L#0 (P#0 31GB)
      L3 L#0 (16MB)
        L2 L#0 (512KB) + L1d L#0 (32KB) + L1i L#0 (32KB) + Core L#0 + PU L#0 (P#0)
        L2 L#1 (512KB) + L1d L#1 (32KB) + L1i L#1 (32KB) + Core L#1 + PU L#1 (P#1)
        L2 L#2 (512KB) + L1d L#2 (32KB) + L1i L#2 (32KB) + Core L#2 + PU L#2 (P#2)
        L2 L#3 (512KB) + L1d L#3 (32KB) + L1i L#3 (32KB) + Core L#3 + PU L#3 (P#3)
      L3 L#1 (16MB)
        L2 L#4 (512KB) + L1d L#4 (32KB) + L1i L#4 (32KB) + Core L#4 + PU L#4 (P#4)
        L2 L#5 (512KB) + L1d L#5 (32KB) + L1i L#5 (32KB) + Core L#5 + PU L#5 (P#5)
        L2 L#6 (512KB) + L1d L#6 (32KB) + L1i L#6 (32KB) + Core L#6 + PU L#6 (P#6)
        L2 L#7 (512KB) + L1d L#7 (32KB) + L1i L#7 (32KB) + Core L#7 + PU L#7 (P#7)
      L3 L#2 (16MB)
        L2 L#8 (512KB) + L1d L#8 (32KB) + L1i L#8 (32KB) + Core L#8 + PU L#8 (P#8)
        L2 L#9 (512KB) + L1d L#9 (32KB) + L1i L#9 (32KB) + Core L#9 + PU L#9 (P#9)
        L2 L#10 (512KB) + L1d L#10 (32KB) + L1i L#10 (32KB) + Core L#10 + PU L#10 (P#10)
        L2 L#11 (512KB) + L1d L#11 (32KB) + L1i L#11 (32KB) + Core L#11 + PU L#11 (P#11)
      L3 L#3 (16MB)
        L2 L#12 (512KB) + L1d L#12 (32KB) + L1i L#12 (32KB) + Core L#12 + PU L#12 (P#12)
        L2 L#13 (512KB) + L1d L#13 (32KB) + L1i L#13 (32KB) + Core L#13 + PU L#13 (P#13)
        L2 L#14 (512KB) + L1d L#14 (32KB) + L1i L#14 (32KB) + Core L#14 + PU L#14 (P#14)
        L2 L#15 (512KB) + L1d L#15 (32KB) + L1i L#15 (32KB) + Core L#15 + PU L#15 (P#15)
      HostBridge
        PCIBridge
          PCI 61:00.0 (InfiniBand)
            Net "ib0"
            OpenFabrics "mlx5_0"
        PCIBridge
          PCIBridge
            PCI 63:00.0 (VGA)
    Group0 L#1
      NUMANode L#1 (P#1 31GB)
      L3 L#4 (16MB)
        L2 L#16 (512KB) + L1d L#16 (32KB) + L1i L#16 (32KB) + Core L#16 + PU L#16 (P#16)
        L2 L#17 (512KB) + L1d L#17 (32KB) + L1i L#17 (32KB) + Core L#17 + PU L#17 (P#17)
        L2 L#18 (512KB) + L1d L#18 (32KB) + L1i L#18 (32KB) + Core L#18 + PU L#18 (P#18)
        L2 L#19 (512KB) + L1d L#19 (32KB) + L1i L#19 (32KB) + Core L#19 + PU L#19 (P#19)
      L3 L#5 (16MB)
        L2 L#20 (512KB) + L1d L#20 (32KB) + L1i L#20 (32KB) + Core L#20 + PU L#20 (P#20)
        L2 L#21 (512KB) + L1d L#21 (32KB) + L1i L#21 (32KB) + Core L#21 + PU L#21 (P#21)
        L2 L#22 (512KB) + L1d L#22 (32KB) + L1i L#22 (32KB) + Core L#22 + PU L#22 (P#22)
        L2 L#23 (512KB) + L1d L#23 (32KB) + L1i L#23 (32KB) + Core L#23 + PU L#23 (P#23)
      L3 L#6 (16MB)
        L2 L#24 (512KB) + L1d L#24 (32KB) + L1i L#24 (32KB) + Core L#24 + PU L#24 (P#24)
        L2 L#25 (512KB) + L1d L#25 (32KB) + L1i L#25 (32KB) + Core L#25 + PU L#25 (P#25)
        L2 L#26 (512KB) + L1d L#26 (32KB) + L1i L#26 (32KB) + Core L#26 + PU L#26 (P#26)
        L2 L#27 (512KB) + L1d L#27 (32KB) + L1i L#27 (32KB) + Core L#27 + PU L#27 (P#27)
      L3 L#7 (16MB)
        L2 L#28 (512KB) + L1d L#28 (32KB) + L1i L#28 (32KB) + Core L#28 + PU L#28 (P#28)
        L2 L#29 (512KB) + L1d L#29 (32KB) + L1i L#29 (32KB) + Core L#29 + PU L#29 (P#29)
        L2 L#30 (512KB) + L1d L#30 (32KB) + L1i L#30 (32KB) + Core L#30 + PU L#30 (P#30)
        L2 L#31 (512KB) + L1d L#31 (32KB) + L1i L#31 (32KB) + Core L#31 + PU L#31 (P#31)
    Group0 L#2
      NUMANode L#2 (P#2 31GB)
    Group0 L#3
      NUMANode L#3 (P#3 31GB)
  Package L#1
    Group0 L#4
      NUMANode L#4 (P#4 31GB)
      HostBridge
        PCIBridge
          PCI e1:00.0 (Ethernet)
            Net "enp225s0f0"
          PCI e1:00.1 (Ethernet)
            Net "enp225s0f1"
    Group0 L#5
      NUMANode L#5 (P#5 31GB)
      HostBridge
        PCIBridge
          PCI c3:00.0 (SATA)
            Block(Disk) "sda"
    Group0 L#6
      NUMANode L#6 (P#6 31GB)
    Group0 L#7
      NUMANode L#7 (P#7 31GB)
```

```text
lscpu
Architecture:        x86_64
CPU op-mode(s):      32-bit, 64-bit
Byte Order:          Little Endian
CPU(s):              128
On-line CPU(s) list: 0-127
Thread(s) per core:  1
Core(s) per socket:  64
Socket(s):           2
NUMA node(s):        8
Vendor ID:           AuthenticAMD
CPU family:          23
Model:               49
Model name:          AMD EPYC 7H12 64-Core Processor
Stepping:            0
CPU MHz:             2092.903
CPU max MHz:         2600.0000
CPU min MHz:         1500.0000
BogoMIPS:            5200.30
Virtualization:      AMD-V
L1d cache:           32K
L1i cache:           32K
L2 cache:            512K
L3 cache:            16384K
NUMA node0 CPU(s):   0-15
NUMA node1 CPU(s):   16-31
NUMA node2 CPU(s):   32-47
NUMA node3 CPU(s):   48-63
NUMA node4 CPU(s):   64-79
NUMA node5 CPU(s):   80-95
NUMA node6 CPU(s):   96-111
NUMA node7 CPU(s):   112-127
Flags:               fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx mmxext fxsr_opt pdpe1gb rdtscp lm constant_tsc rep_good nopl nonstop_tsc cpuid extd_apicid aperfmperf pni pclmulqdq monitor ssse3 fma cx16 sse4_1 sse4_2 x2apic movbe popcnt aes xsave avx f16c rdrand lahf_lm cmp_legacy svm extapic cr8_legacy abm sse4a misalignsse 3dnowprefetch osvw ibs skinit wdt tce topoext perfctr_core perfctr_nb bpext perfctr_llc mwaitx cpb cat_l3 cdp_l3 hw_pstate ssbd mba ibrs ibpb stibp vmmcall fsgsbase bmi1 avx2 smep bmi2 cqm rdt_a rdseed adx clflushopt clwb sha_ni xsaveopt xsavec xgetbv1 xsaves cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local clzero irperf xsaveerptr wbnoinvd arat npt lbrv svm_lock nrip_save tsc_scale vmcb_clean flushbyasid decodeassists pausefilter pfthreshold avic v_vmsave_vmload vgif v_spec_ctrl umip rdpid overflow_recov succor smca sme sev sev_es
```

| Level | Entity | Count |
|-------|--------|-------|
| Node | aion-0105 | 1 |
| Physical socket | `Package L#0`, `Package L#1` | 2 |
| NUMA nodes | L#0 – L#7 | 8 (4 per socket) |
| Cores per NUMA | 8 | 64 total |
| Memory per NUMA | 31GB | ~250GB total |

---

On `Iris`

```text
1 [bjiang@iris-187 ~](4103746 2N/32T/31,1CN)$ hostname
iris-187
127 [bjiang@iris-187 ~](4103746 2N/32T/31,1CN)$ module load system/hwloc
0 [bjiang@iris-187 ~](4103746 2N/32T/31,1CN)$ lstopo
Machine (3022GB total)
  Package L#0
    NUMANode L#0 (P#0 754GB)
    HostBridge
      PCI 00:11.5 (SATA)
      PCI 00:17.0 (SATA)
      PCIBridge
        PCI 01:00.0 (Ethernet)
          Net "eth0"
        PCI 01:00.1 (Ethernet)
          Net "eth2"
      PCIBridge
        PCIBridge
          PCI 03:00.0 (VGA)
    HostBridge
      PCIBridge
        PCI 17:00.0 (Ethernet)
          Net "eth1"
        PCI 17:00.1 (Ethernet)
          Net "eth3"
    HostBridge
      PCIBridge
        PCI 33:00.0 (InfiniBand)
          Net "ib0"
          OpenFabrics "mlx5_0"
        PCI 33:00.1 (InfiniBand)
          Net "ib1"
          OpenFabrics "mlx5_1"
  Package L#1
    NUMANode L#1 (P#1 756GB)
    L3 L#0 (39MB)
      L2 L#0 (1024KB) + L1d L#0 (32KB) + L1i L#0 (32KB) + Core L#0 + PU L#0 (P#5)
      L2 L#1 (1024KB) + L1d L#1 (32KB) + L1i L#1 (32KB) + Core L#1 + PU L#1 (P#9)
      L2 L#2 (1024KB) + L1d L#2 (32KB) + L1i L#2 (32KB) + Core L#2 + PU L#2 (P#13)
      L2 L#3 (1024KB) + L1d L#3 (32KB) + L1i L#3 (32KB) + Core L#3 + PU L#3 (P#17)
      L2 L#4 (1024KB) + L1d L#4 (32KB) + L1i L#4 (32KB) + Core L#4 + PU L#4 (P#21)
      L2 L#5 (1024KB) + L1d L#5 (32KB) + L1i L#5 (32KB) + Core L#5 + PU L#5 (P#25)
      L2 L#6 (1024KB) + L1d L#6 (32KB) + L1i L#6 (32KB) + Core L#6 + PU L#6 (P#29)
      L2 L#7 (1024KB) + L1d L#7 (32KB) + L1i L#7 (32KB) + Core L#7 + PU L#7 (P#33)
      L2 L#8 (1024KB) + L1d L#8 (32KB) + L1i L#8 (32KB) + Core L#8 + PU L#8 (P#37)
      L2 L#9 (1024KB) + L1d L#9 (32KB) + L1i L#9 (32KB) + Core L#9 + PU L#9 (P#45)
      L2 L#10 (1024KB) + L1d L#10 (32KB) + L1i L#10 (32KB) + Core L#10 + PU L#10 (P#49)
      L2 L#11 (1024KB) + L1d L#11 (32KB) + L1i L#11 (32KB) + Core L#11 + PU L#11 (P#53)
      L2 L#12 (1024KB) + L1d L#12 (32KB) + L1i L#12 (32KB) + Core L#12 + PU L#12 (P#57)
      L2 L#13 (1024KB) + L1d L#13 (32KB) + L1i L#13 (32KB) + Core L#13 + PU L#13 (P#61)
      L2 L#14 (1024KB) + L1d L#14 (32KB) + L1i L#14 (32KB) + Core L#14 + PU L#14 (P#65)
      L2 L#15 (1024KB) + L1d L#15 (32KB) + L1i L#15 (32KB) + Core L#15 + PU L#15 (P#69)
      L2 L#16 (1024KB) + L1d L#16 (32KB) + L1i L#16 (32KB) + Core L#16 + PU L#16 (P#73)
    HostBridge
      PCIBridge
        PCI 48:00.0 (NVMExp)
          Block(Disk) "nvme0n1"
  Package L#2
    NUMANode L#2 (P#2 756GB)
    L3 L#1 (39MB)
      L2 L#17 (1024KB) + L1d L#17 (32KB) + L1i L#17 (32KB) + Core L#17 + PU L#17 (P#2)
      L2 L#18 (1024KB) + L1d L#18 (32KB) + L1i L#18 (32KB) + Core L#18 + PU L#18 (P#6)
      L2 L#19 (1024KB) + L1d L#19 (32KB) + L1i L#19 (32KB) + Core L#19 + PU L#19 (P#10)
      L2 L#20 (1024KB) + L1d L#20 (32KB) + L1i L#20 (32KB) + Core L#20 + PU L#20 (P#14)
      L2 L#21 (1024KB) + L1d L#21 (32KB) + L1i L#21 (32KB) + Core L#21 + PU L#21 (P#18)
      L2 L#22 (1024KB) + L1d L#22 (32KB) + L1i L#22 (32KB) + Core L#22 + PU L#22 (P#22)
      L2 L#23 (1024KB) + L1d L#23 (32KB) + L1i L#23 (32KB) + Core L#23 + PU L#23 (P#26)
      L2 L#24 (1024KB) + L1d L#24 (32KB) + L1i L#24 (32KB) + Core L#24 + PU L#24 (P#30)
      L2 L#25 (1024KB) + L1d L#25 (32KB) + L1i L#25 (32KB) + Core L#25 + PU L#25 (P#34)
      L2 L#26 (1024KB) + L1d L#26 (32KB) + L1i L#26 (32KB) + Core L#26 + PU L#26 (P#38)
      L2 L#27 (1024KB) + L1d L#27 (32KB) + L1i L#27 (32KB) + Core L#27 + PU L#27 (P#42)
      L2 L#28 (1024KB) + L1d L#28 (32KB) + L1i L#28 (32KB) + Core L#28 + PU L#28 (P#46)
      L2 L#29 (1024KB) + L1d L#29 (32KB) + L1i L#29 (32KB) + Core L#29 + PU L#29 (P#50)
      L2 L#30 (1024KB) + L1d L#30 (32KB) + L1i L#30 (32KB) + Core L#30 + PU L#30 (P#54)
      L2 L#31 (1024KB) + L1d L#31 (32KB) + L1i L#31 (32KB) + Core L#31 + PU L#31 (P#58)
      L2 L#32 (1024KB) + L1d L#32 (32KB) + L1i L#32 (32KB) + Core L#32 + PU L#32 (P#62)
      L2 L#33 (1024KB) + L1d L#33 (32KB) + L1i L#33 (32KB) + Core L#33 + PU L#33 (P#66)
      L2 L#34 (1024KB) + L1d L#34 (32KB) + L1i L#34 (32KB) + Core L#34 + PU L#34 (P#70)
      L2 L#35 (1024KB) + L1d L#35 (32KB) + L1i L#35 (32KB) + Core L#35 + PU L#35 (P#74)
      L2 L#36 (1024KB) + L1d L#36 (32KB) + L1i L#36 (32KB) + Core L#36 + PU L#36 (P#78)
      L2 L#37 (1024KB) + L1d L#37 (32KB) + L1i L#37 (32KB) + Core L#37 + PU L#37 (P#82)
      L2 L#38 (1024KB) + L1d L#38 (32KB) + L1i L#38 (32KB) + Core L#38 + PU L#38 (P#86)
      L2 L#39 (1024KB) + L1d L#39 (32KB) + L1i L#39 (32KB) + Core L#39 + PU L#39 (P#90)
  Package L#3
    NUMANode L#3 (P#3 756GB)
    L3 L#2 (39MB)
      L2 L#40 (1024KB) + L1d L#40 (32KB) + L1i L#40 (32KB) + Core L#40 + PU L#40 (P#23)
      L2 L#41 (1024KB) + L1d L#41 (32KB) + L1i L#41 (32KB) + Core L#41 + PU L#41 (P#27)
      L2 L#42 (1024KB) + L1d L#42 (32KB) + L1i L#42 (32KB) + Core L#42 + PU L#42 (P#31)
      L2 L#43 (1024KB) + L1d L#43 (32KB) + L1i L#43 (32KB) + Core L#43 + PU L#43 (P#35)
      L2 L#44 (1024KB) + L1d L#44 (32KB) + L1i L#44 (32KB) + Core L#44 + PU L#44 (P#39)
      L2 L#45 (1024KB) + L1d L#45 (32KB) + L1i L#45 (32KB) + Core L#45 + PU L#45 (P#43)
      L2 L#46 (1024KB) + L1d L#46 (32KB) + L1i L#46 (32KB) + Core L#46 + PU L#46 (P#47)
      L2 L#47 (1024KB) + L1d L#47 (32KB) + L1i L#47 (32KB) + Core L#47 + PU L#47 (P#51)
      L2 L#48 (1024KB) + L1d L#48 (32KB) + L1i L#48 (32KB) + Core L#48 + PU L#48 (P#55)
      L2 L#49 (1024KB) + L1d L#49 (32KB) + L1i L#49 (32KB) + Core L#49 + PU L#49 (P#59)
      L2 L#50 (1024KB) + L1d L#50 (32KB) + L1i L#50 (32KB) + Core L#50 + PU L#50 (P#63)
      L2 L#51 (1024KB) + L1d L#51 (32KB) + L1i L#51 (32KB) + Core L#51 + PU L#51 (P#67)
      L2 L#52 (1024KB) + L1d L#52 (32KB) + L1i L#52 (32KB) + Core L#52 + PU L#52 (P#71)
      L2 L#53 (1024KB) + L1d L#53 (32KB) + L1i L#53 (32KB) + Core L#53 + PU L#53 (P#75)
      L2 L#54 (1024KB) + L1d L#54 (32KB) + L1i L#54 (32KB) + Core L#54 + PU L#54 (P#79)
      L2 L#55 (1024KB) + L1d L#55 (32KB) + L1i L#55 (32KB) + Core L#55 + PU L#55 (P#83)
      L2 L#56 (1024KB) + L1d L#56 (32KB) + L1i L#56 (32KB) + Core L#56 + PU L#56 (P#87)
      L2 L#57 (1024KB) + L1d L#57 (32KB) + L1i L#57 (32KB) + Core L#57 + PU L#57 (P#91)
      L2 L#58 (1024KB) + L1d L#58 (32KB) + L1i L#58 (32KB) + Core L#58 + PU L#58 (P#95)
      L2 L#59 (1024KB) + L1d L#59 (32KB) + L1i L#59 (32KB) + Core L#59 + PU L#59 (P#99)
      L2 L#60 (1024KB) + L1d L#60 (32KB) + L1i L#60 (32KB) + Core L#60 + PU L#60 (P#103)
      L2 L#61 (1024KB) + L1d L#61 (32KB) + L1i L#61 (32KB) + Core L#61 + PU L#61 (P#107)
```

```text
lscpu
Architecture:        x86_64
CPU op-mode(s):      32-bit, 64-bit
Byte Order:          Little Endian
CPU(s):              112
On-line CPU(s) list: 0-111
Thread(s) per core:  1
Core(s) per socket:  28
Socket(s):           4
NUMA node(s):        4
Vendor ID:           GenuineIntel
CPU family:          6
Model:               85
Model name:          Intel(R) Xeon(R) Platinum 8180M CPU @ 2.50GHz
Stepping:            4
CPU MHz:             3800.001
CPU max MHz:         3800.0000
CPU min MHz:         1000.0000
BogoMIPS:            5000.00
Virtualization:      VT-x
L1d cache:           32K
L1i cache:           32K
L2 cache:            1024K
L3 cache:            39424K
NUMA node0 CPU(s):   0,4,8,12,16,20,24,28,32,36,40,44,48,52,56,60,64,68,72,76,80,84,88,92,96,100,104,108
NUMA node1 CPU(s):   1,5,9,13,17,21,25,29,33,37,41,45,49,53,57,61,65,69,73,77,81,85,89,93,97,101,105,109
NUMA node2 CPU(s):   2,6,10,14,18,22,26,30,34,38,42,46,50,54,58,62,66,70,74,78,82,86,90,94,98,102,106,110
NUMA node3 CPU(s):   3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,95,99,103,107,111
Flags:               fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb cat_l3 cdp_l3 invpcid_single pti intel_ppin ssbd mba ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm mpx rdt_a avx512f avx512dq rdseed adx smap clflushopt clwb intel_pt avx512cd avx512bw avx512vl xsaveopt xsavec xgetbv1 xsaves cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts pku ospke md_clear flush_l1d arch_capabilities
```
|Level|Entity|Count|
|---|---|---|
|**Node**|`iris-187`|1|
|**Physical Sockets**|`Package L#0`, `L#1`, `L#2`, `L#3`|4|
|**NUMA Nodes**|`L#0`, `L#1`, `L#2`, `L#3`|4 (1 per socket)|
|**Cores per NUMA**|28 (Core(s) per socket)|128 total (4 NUMA × 32 cores)|
|**Threads per Core**|2 (PU per core for `L#1`-`L#3`)|128 Processing Units (PUs) total|
|**Memory per NUMA**|~754–756 GB|~3022 GB total (reported by `lstopo`)|
|**L3 Cache**|One L3 per socket (39MB each)|4 × 39MB|
|**L2/L1 Caches**|1MB L2 and 64KB L1 (32KB d + 32KB i) per core|128 of each|

---

### Step 3. **Run benchmarks manually** to test latency/bandwidth between

In HPC system:
- **Compute node** = a physical **server** in the cluster (can have 1+ sockets). e.g. `iris-187`
	- This is the **physical machine** in the ULHPC cluster. It's also called a **node** in the cluster.
- **Socket** = a physical **CPU chip** on a motherboard. e.g. `L#0`
	- Each socket is associated with some **NUMA nodes**.
- **NUMA node** = a region of memory and CPU cores that are close to each other (same socket).
	- Very **fastest** possible communication (shared L3 cache, no memory copying)
	- This may not work for `Iris`
-  **Cores**
	- A core is an independent processing unit within a CPU. A multi-core processor contains several cores, each capable of executing its own thread or multiple threads in an SMT system.
-  **Threads**
	- Threads are the smallest unit of execution within a process. On modern CPUs, a single physical core can run multiple hardware threads using Simultaneous Multithreading (SMT). Each thread represents an independent stream of instructions.

---

- Same NUMA node
- Same physical socket (but different NUMA node)
- same compute node but different sockets 
- same compute node but different nodes


####  ✅ Test Design Overview

|Test ID|Process Placement|Motivation|
|---|---|---|
|**T1**|Same core, different threads (SMT siblings)|Measure overhead of SMT sharing|
|**T2**|Same socket, different physical cores|Measure core-to-core performance (ideal intra-socket)|
|**T3**|Different sockets|Measure NUMA penalty within a node|
|**T4**|Different NUMA domains|Measure NUMA domain communication overhead|
|**T5**|Farthest possible distance (max hop)|Worst-case latency test within a node|
|**T6**|Near sockets (adjacent cores)|Intermediate behavior for nearby cores|
|**T7**|Automatic placement (no affinity)|Baseline for scheduler-placed tasks|
|**T8**|Bound to specific NUMA nodes|Measure performance stability within a NUMA domain|
|**T9**|Basic Cross-Node Communication|Measure interconnect performance|
|**T10**|Multi-Node with thread binding|Thread binding across nodes|
|**T11**|Multi-Node with socket binding|Socket-level binding across nodes|
|**T12**|Multi-Node with core binding|Core-level binding across nodes|
|**T13**|Multi-Node with NUMA domain binding|NUMA domain binding across nodes|

---

#### 🔍 Details for Each Test

##### 🔸 T1: Same core, SMT siblings

- Process 1: Core 0, PU 0 (e.g., `CPU 0`)
    
- Process 2: Core 0, PU 1 (e.g., `CPU 1`)
    
- **Command example**:
    
```bash
./connect.sh --nodes 2 --cpus 2

module load env/testing/2023b
module load system/hwloc
cd ~/hpc-project/scripts/
./1.Install-OSU-Micro-Benchmarks.sh -m local
cd  $EBROOTOSUMINMICROMINBENCHMARKS/libexec/osu-micro-benchmarks/mpi/one-sided/
srun -N1 -n 2 --cpu-bind=threads ./osu_get_latency
```
    

##### 🔸 T2: Same socket, different cores

- Process 1: Core 0, PU 0    
- Process 2: Core 1, PU 2 (both in Socket 0)    
- **Motivation**: Best intra-socket communication    
- **Binding**: `0,2`
```bash
srun -N1 -n 2 --cpu-bind=cores ./osu_get_latency
```

##### 🔸 T3: Different sockets

- Process 1: Core 0, PU 0 (Socket 0)    
- Process 2: Core 8, PU 16 (Socket 1)
    
- **Binding**: `0,16`
    
- **Motivation**: Expose NUMA communication overhead
```bash
srun -N1 -n 2 --cpu-bind=sockets ./osu_get_latency
```


##### 🔸 T4: Different NUMA domains

```bash
# Request 2 nodes with 1 process per node, bind each process to core 0 on its node
srun -N2 -n2 --ntasks-per-node=1 --cpu-bind=ldoms ./osu_get_latency
```

##### 🔸 T5: Max hop / farthest cores

- Use `hwloc-distances` or `lstopo` to find the most distant cores (e.g., cross-NUMA and non-L3 sharing)
    
- Might be something like `0` and `31`

```bash
# Binding to most distant cores (determined from topology)
srun -N1 -n1 bash -c "cat /proc/self/status | grep Cpus_allowed_list"

srun -N1 -n2 bash -c "taskset -pc \$\$; ./osu_get_latency"

srun -N1 -n2 --cpu-bind=map_cpu:3,111 ./osu_get_latency
```

##### 🔸 T6: Neighboring sockets

- Pick adjacent NUMA nodes sharing cache levels (e.g., L3)    
- Moderate latency and bandwidth compared to T2 and T3

```bash
# Select cores from adjacent NUMA domains
srun -N1 -n2 --cpu-bind=map_ldom:0,3 ./osu_get_latency
```
    

##### 🔸 T7: No binding

- Let Slurm decide placement    
- Helps detect problems with default affinity policy
    
- **Command**:    
```bash
srun -N1 -n2 --cpu-bind=None ./osu_get_latency
```

##### 🔸 T8: NUMA-aware  placement
- Explicitly bind both processes to a NUMA node (e.g., `numactl --cpunodebind=0`)
    
- Test intra-NUMA node consistency
```bash
# Bind both processes to NUMA node 0
srun -N1 -n2 bash -c 'numactl --cpunodebind=1 --membind=2 ./osu_get_latency'
```
**--cpunodebind=2**: This option forces the process to run only on the CPUs that belong to NUMA node 2.  
**--membind=2**: This option forces the process to allocate memory from the memory associated with NUMA node 2.

##### 🔸 T9: Basic Cross-Node Communication

- **Placement**: Processes on separate physical nodes
- **Motivation**: Measure interconnect performance and network latency/bandwidth

```bash
# Request 2 nodes with 1 process per node
srun -N2 -n2 --ntasks-per-node=1 ./osu_get_latency
```



##### 🔸 T10: Multi-Node with thread binding

```bash
# Request 2 nodes with 1 process per node, bind each process to core 0 on its node
srun -N2 -n2 --ntasks-per-node=1 --cpu-bind=threads ./osu_get_latency
```

##### 🔸 T11: Multi-Node with socket binding

```bash
# Request 2 nodes with 1 process per node, bind each process to core 0 on its node
srun -N2 -n2 --ntasks-per-node=1 --cpu-bind=scokets ./osu_get_latency
```


##### 🔸 T12: Multi-Node with core binding

```bash
# Request 2 nodes with 1 process per node, bind each process to core 0 on its node
srun -N2 -n2 --ntasks-per-node=1 --cpu-bind=cores ./osu_get_latency
```


##### 🔸 T13: Multi-Node with NUMA domain binding

```bash
# Request 2 nodes with 1 process per node, bind each process to core 0 on its node
srun -N2 -n2 --ntasks-per-node=1 --cpu-bind=ldoms ./osu_get_latency
```


---

### Step 4. **Write regression tests in ReFrame**

- Automate running the benchmarks

- Run on both **IRIS** and **Aion**

- Source binaries in different ways (precompiled, compiled from source, etc.)

```bash
module use /opt/apps/easybuild/systems/aion/rhel810-20250216/2023b/epyc/modules/all
module load env/testing/2023b
module load devel/ReFrame/4.7.3-GCCcore-13.2.0

module load devel/ReFrame/4.7.4-GCCcore-13.2.0
cd ~/hpc-project/tests
reframe --config-file ulhpc.py --checkpath 4.1-OSU-BENCHMARK-ONESIDE-TEST.py --name 'OSUGetNumaAwareTest' --run
```

### Step 5. **Collect baseline/reference values** (latency, bandwidth)

```bash
REFERENCE_VALUES = {
...
}
```

### Step 6. **Generate figures** (e.g., bar plots of latency/bandwidth vs core location)

```bash

```

### Step 7. **Write the final report**

- Describe setup
- Explain results
- Discuss what you learned about the system's topology and communication behavior
    
---


# 📊 **Expected Performance (Baseline Values)**

Use these as **reference values** in your regression tests:

| Test | Cluster | Config | Expected Value |
|-------------|---------|---------------|---------------------|
| osu_latency | Aion | Intra-node | ~2.3 µs |
| osu_latency | Aion | Inter-node | ~3.9 µs |
| osu_bw | Aion | Any config | ~12,000 MB/s |

Your ReFrame tests should **fail** if performance drops significantly from these, **unless** such a drop is expected (e.g., system update).

---

# 📂 **What You Need to Deliver**

## 1. ✅ ReFrame Test Scripts

- For each binary source (local, EasyBuild, EESSI)
- For each scenario (intra-socket, inter-socket, inter-node)
- For each cluster (IRIS and Aion)
- Fully documented

## 2. 📈 Performance Report

- Graphs showing results for each scenario + binary source
- Analysis explaining:
- Why you chose specific test cases
- Why your reference values are valid
- What changes might affect those values

## 3. 📁 Git Repository

- All scripts, configs, and documentation
- Instructions to clone and run the tests

## 4. 🎤 Final Evaluation

- 10-minute presentation: goals, methods, findings
- 15–20 minute live demo:
- Start from scratch (clone repo)
- Load modules
- Run tests in ReFrame
- Show that results match your report

---

# 🧠 Strategy Tips

- Start testing **intra-node** cases first (easier to debug).

- Use `hwloc` to **pin processes** to specific sockets/cores.

- Use ReFrame's **performance reference system** to define pass/fail thresholds.

- Keep your test scripts **modular** so you can reuse logic across scenarios and clusters.


