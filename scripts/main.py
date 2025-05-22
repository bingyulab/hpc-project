import os
import sys
import subprocess
import datetime
import argparse
from pathlib import Path


def log(message, log_file):
    """Log message to both console and file"""
    print(message)
    with open(log_file, 'a') as f:
        f.write(message + '\n')
        
log_dir = os.path.expanduser("~/hpc-project/log")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "test_run.log")

timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log(f"Starting HPC benchmark test suite at {timestamp}", log_file)
log("=======================================", log_file)

# Path definitions
script_dir = os.path.expanduser("~/hpc-project/scripts")
install_script = os.path.join(script_dir, "1.Install-OSU-Micro-Benchmarks.sh")
test_script = os.path.join(script_dir, "3.Tests.sh")

def run_command(cmd, log_file, shell=False):
    """Run a command and log its output to both console and file"""
    log(f"Running command: {cmd}", log_file)
    process = subprocess.run(
        cmd, shell=True, capture_output=True, text=True)
    
    # Read and log output line by line
    log(process.stdout, log_file)
    
    # Wait for the process to complete and get exit code
    exit_code = process.returncode
    return exit_code

def run_test_for_method(method, log_file, script_dir):
    """Run tests for a specific installation method"""    
    log("=======================================", log_file)
    log(f"Running tests for method: {method}", log_file)
    log("=======================================", log_file)
    
    # Define environment file name
    env_file = f"/tmp/osu_env_{method}.sh"
    
    # Step 1: Run the installation script with method
    log(f"Installing OSU benchmarks ({method})...", log_file)
    exit_code = run_command(f"{install_script} --method {method}", log_file)
    if exit_code != 0:
        log(f"ERROR: Installation script failed for {method}", log_file)
        return 1
    
    # Step 2: Prepare environment setup commands
    
    # Source environment file if it exists
    if os.path.isfile(env_file):
        log(f"Sourcing environment file: {env_file}", log_file)
        run_command(f"source {env_file}", log_file, shell=True)
    else:
        log(f"Warning: Environment file not found at {env_file}", log_file)
        log("Continuing with existing environment", log_file)
    
    # Step 3: Load modules if environment variable not set
    if "EBROOTOSUMINMICROMINBENCHMARKS" not in os.environ:
        log("Warning: EBROOTOSUMINMICROMINBENCHMARKS not set, attempting to load modules directly", log_file)
        if method == "easybuild":
            run_command("module load tools/EasyBuild/5.0.0 2>/dev/null || true", log_file, shell=True)
            run_command("module load perf/OSU-Micro-Benchmarks/7.2-gompi-2023b 2>/dev/null || true", log_file, shell=True)
        elif method == "eessi":
            run_command("module load EESSI 2>/dev/null || true", log_file, shell=True)
            run_command("module load OSU-Micro-Benchmarks/7.2-gompi-2023b 2>/dev/null || true", log_file, shell=True)
        
        elif method == "local":            
            INSTALL_DIR=os.path.expanduser(f"~/osu-micro-benchmarks-7.2/build")
            run_command(f'export EBROOTOSUMINMICROMINBENCHMARKS={INSTALL_DIR}', log_file, shell=True)
            log("Using local OSU installation", log_file)
        # print(f"EBROOTOSUMINMICROMINBENCHMARKS={os.environ['EBROOTOSUMINMICROMINBENCHMARKS']}")
    # Step 4: Run the test script
    log(f"Running benchmark tests for {method}...", log_file)
    log("---------------------------------------", log_file)
    
    # Add export of OSU_METHOD and test script command
    exit_code = run_command(f"export OSU_METHOD={method}", log_file, shell=True)
    exit_code = run_command(f"{test_script} {method}", log_file, shell=True)

    # Step 5: Report results
    if exit_code == 0:
        log(f"✅ Tests completed successfully for {method}", log_file)
    else:
        log(f"❌ Tests completed with errors for {method} (exit code: {exit_code})", log_file)
    
    return exit_code

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run HPC benchmark tests")
    parser.add_argument("--method", nargs="?", default="local", 
                      choices=["local", "easybuild", "eessi", "all"],
                      help="Installation method (default: local)")
    args = parser.parse_args()
    
    install_method = args.method
    
    # Setup logging    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log(f"Starting HPC benchmark test suite at {timestamp}", log_file)
    log(f"Installation method: {install_method}", log_file)
    log("=======================================", log_file)
              
    # Initialize overall exit code
    overall_exit_code = 0
    
    # Run tests based on selected method
    if install_method == "all":
        # Run tests for each method
        methods = ["local", "easybuild", "eessi"]
        for method in methods:
            method_exit_code = run_test_for_method(method, log_file, script_dir)
            
            # Keep track of errors
            if method_exit_code != 0:
                overall_exit_code = method_exit_code
            
            # Add some separation between test runs
            log("", log_file)
            log("---------------------------------------", log_file)
            log("", log_file)
    else:
        # Run only the specified method
        overall_exit_code = run_test_for_method(install_method, log_file, script_dir)
    
    # Final summary
    log("=======================================", log_file)
    if overall_exit_code == 0:
        log("✅ All test runs completed successfully", log_file)
    else:
        log("❌ One or more test runs had errors", log_file)
    
    log(f"Log file: {log_file}", log_file)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log(f"Completed at: {timestamp}", log_file)
    
    return overall_exit_code

if __name__ == "__main__":
    sys.exit(main())