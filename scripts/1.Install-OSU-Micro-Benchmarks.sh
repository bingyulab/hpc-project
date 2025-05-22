#!/bin/bash

# Default values
INSTALL_METHOD="local"
OSU_VERSION="7.2"
VERIFY="false"
TEMP_ENV_FILE="/tmp/osu_env_${INSTALL_METHOD}.sh"
rm "$TEMP_ENV_FILE" 2>/dev/null || true

# Parse command line options
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -m|--method) INSTALL_METHOD="$2"; shift ;;
        -v|--osu-version|--version) OSU_VERSION="$2"; shift ;;
        --verify) VERIFY="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

VERIFY_BINARIES=("osu_get_latency" "osu_get_bw")

print_header() {
    echo -e "\n========== $1 ==========\n"
}

verify_osu() {
    local exe_path="${EBROOTOSUMINMICROMINBENCHMARKS}/libexec/osu-micro-benchmarks/mpi/one-sided"
    echo "Verifying OSU Benchmarks at: $exe_path"
    cd "$exe_path" || { echo "❌ Failed to access $exe_path"; return 1; }
    for binary in "${VERIFY_BINARIES[@]}"; do
        if [[ -x "./$binary" ]]; then
            echo "Running: srun -n 2 ./$binary"
            srun -n 2 ./"$binary" || echo "❌ $binary failed"
        else
            echo "❌ $binary not found in $exe_path"
        fi
    done
    cd ~/hpc-project || true
}

install_local() {
    print_header "Local Compilation"
    INSTALL_DIR=~/osu-micro-benchmarks-${OSU_VERSION}
    BUILD_DIR=${INSTALL_DIR}/build
    EBROOTOSUMINMICROMINBENCHMARKS="$BUILD_DIR"
    export EBROOTOSUMINMICROMINBENCHMARKS

    if [[ -d "$EBROOTOSUMINMICROMINBENCHMARKS/libexec/osu-micro-benchmarks/mpi/one-sided" ]]; then
        echo "✅ OSU Benchmarks already compiled locally at $BUILD_DIR"
        echo "export EBROOTOSUMINMICROMINBENCHMARKS=$EBROOTOSUMINMICROMINBENCHMARKS" >> "$TEMP_ENV_FILE"
        echo "export PATH=\"\$EBROOTOSUMINMICROMINBENCHMARKS/libexec/osu-micro-benchmarks/mpi/one-sided:\$PATH\"" >> "$TEMP_ENV_FILE"
	    [[ "$VERIFY" == "true" || "$VERIFY" == "yes" ]] && verify_osu
        return
    fi

    echo "🛠️ Installing OSU Benchmarks locally..."
    mkdir -p ~/project
    cd ~/project || exit 1
    wget https://mvapich.cse.ohio-state.edu/download/mvapich/osu-micro-benchmarks-${OSU_VERSION}.tar.gz
    tar -zxvf osu-micro-benchmarks-${OSU_VERSION}.tar.gz
    cd osu-micro-benchmarks-${OSU_VERSION} || exit 1

    mkdir -p build && cd build
    module load toolchain/foss/2023b
    ../configure CC=mpicc CFLAGS=-I$(pwd)/../util --prefix=$(pwd)
    make -j && make install

    echo "export EBROOTOSUMINMICROMINBENCHMARKS=EBROOTOSUMINMICROMINBENCHMARKS" >> "$TEMP_ENV_FILE"
    [[ "$VERIFY" == "true" || "$VERIFY" == "yes" ]] && verify_osu

}

install_easybuild() {
    print_header "EasyBuild Method"
    module purge
    module load tools/EasyBuild/5.0.0
    module load toolchain/gompi/2023b

    if module avail perf/OSU-Micro-Benchmarks/${OSU_VERSION}-gompi-2023b 2>&1 | grep -q "$OSU_VERSION"; then
        echo "✅ OSU module found in EasyBuild"
        
    else
        echo "⚠️ Module not found, trying to build with EasyBuild..."
        eb ~/.local/easybuild/software/EasyBuild/5.0.0/easybuild/easyconfigs/o/OSU-Micro-Benchmarks/OSU-Micro-Benchmarks-${OSU_VERSION}-gompi-2023b.eb
    fi

    echo "module load perf/OSU-Micro-Benchmarks/${OSU_VERSION}-gompi-2023b" >> "$TEMP_ENV_FILE"
    echo "export PATH=\"\$EBROOTOSUMINMICROMINBENCHMARKS/libexec/osu-micro-benchmarks/mpi/one-sided:\$PATH\"" >> "$TEMP_ENV_FILE"
    module use "${EASYBUILD_PREFIX}/modules/all"
    module load perf/OSU-Micro-Benchmarks/${OSU_VERSION}-gompi-2023b 
    [[ "$VERIFY" == "true" || "$VERIFY" == "yes" ]] && verify_osu
}

install_eessi() {
    print_header "EESSI Method"
    module purge

    if ! module avail EESSI 2>&1 | grep -q EESSI; then
        echo "❌ EESSI module not available"
        return 1
    fi

    module load EESSI

    if module avail OSU-Micro-Benchmarks/${OSU_VERSION}-gompi-2023b 2>&1 | grep -q "$OSU_VERSION"; then
        echo "✅ Found OSU Benchmarks in EESSI"
        echo "module load EESSI" >> "$TEMP_ENV_FILE"
        echo "module load OSU-Micro-Benchmarks/${OSU_VERSION}-gompi-2023b" >> "$TEMP_ENV_FILE"
        echo "export PATH=\"\$EBROOTOSUMINMICROMINBENCHMARKS/libexec/osu-micro-benchmarks/mpi/one-sided:\$PATH\"" >> "$TEMP_ENV_FILE"
        module load OSU-Micro-Benchmarks/${OSU_VERSION}-gompi-2023b
        [[ "$VERIFY" == "true" || "$VERIFY" == "yes" ]] && verify_osu
    else
        echo "❌ OSU Benchmarks module not found in EESSI"
    fi
}

# Main entry point
case "$INSTALL_METHOD" in
    local)
        install_local
        ;;
    easybuild)
        install_easybuild
        ;;
    eessi)
        install_eessi
        ;;
    *)
        echo "❌ Invalid installation method: $INSTALL_METHOD"
        echo "Usage: $0 --method [local|easybuild|eessi] --osu-version <VERSION>"
        exit 1
        ;;
esac

# Print message to source env
if [[ -f "$TEMP_ENV_FILE" ]]; then
    echo -e "\n✅ Done. To load the environment in your current shell, run:\n"
    echo "    source $TEMP_ENV_FILE"
    echo
fi

