# 🔍 **MPI Performance Testing Suite**

A comprehensive **performance testing framework** using **ReFrame** to measure and monitor MPI communication performance on the **ULHPC clusters** (IRIS and Aion).

## Project Goal

This project builds a testing suite to measure MPI communication latency and bandwidth, helping to detect unexpected performance drops over time due to system updates, hardware changes, or other factors.

## 🔧 **Technologies**

- **ReFrame**: Framework for automated testing and result tracking
- **OSU Micro-Benchmarks (OMB)**: Industry-standard MPI benchmarking tools
	- `osu_latency`: Measures communication delay
	- `osu_bw`: Measures communication throughput

## 📋 **Requirements**

- **Target Clusters**: 
	- IRIS (CPU nodes only)
	- Aion

- **Benchmark Parameters**:
	- `osu_latency`: 8192 bytes message size
	- `osu_bw`: 1MB (1,048,576 bytes) message size

- **Testing Environments**:
	- Local build
	- EasyBuild
	- EESSI

## 🧪 **Test Scenarios**

This suite measures MPI performance across four key communication scenarios:

1. **Same NUMA node**: Both processes on the same NUMA node
2. **Different NUMA node**: Processes on the same physical socket but different NUMA nodes
3. **Different Sockets**: Processes on the same compute node but different sockets
4. **Different nodes**: Processes running on separate compute nodes

## 📦 **Installation**

Connect to HPC server:
```bash
salloc -N 2 -n 2 --exclusive 
```

Install OSU Micro-Benchmarks using one of these methods:

```bash
cd scripts

# Local installation
./1.Install-OSU-Micro-Benchmarks.sh --method local
# Source the generated environment file
source /tmp/osu_env_*.sh

# EESSI installation
./1.Install-OSU-Micro-Benchmarks.sh --method eessi

# EasyBuild installation
./1.Install-OSU-Micro-Benchmarks.sh --method easybuild
```

## 🚀 **Usage**

### Hardware Detection

Analyze and detect the cluster hardware topology:
```bash
cd scripts
./2.Hardware-Detection.sh
```
### Running Tests manully  

```bash
cd scripts
./3.Tests.sh
```
Note, there are some bugs of python does not successfully load environmental vairable. I have not fixed yet. 

Or, simply run
```bash
./run-test.sh
```
### Running Tests with ReFrame

Execute the complete test suite:
```bash
cd tests/
./run.sh
```

This will automatically run all benchmark tests and generate performance reports.

## 📊 **Results**

Test results are stored in the ReFrame output directory and can be used to track performance trends over time.

## 👥 **Author and Contributions**

This project was developed as part of a group coursework in High-Performance Computing (HPC). 

The manual testing components were contributed by team members but have been temporarily removed. Future updates may include a reimplementation of these components.
