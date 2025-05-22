module load env/testing/2023b

module load devel/ReFrame/4.7.4-GCCcore-13.2.0

CLUSTER_NAME=$(hostname -f | cut -d. -f1 | cut -d- -f1)

# rm -rf ~/hpc-project/scripts/bind_*.sh
rm -rf ~/hpc-project/reframe-output/*
rm -rf ~/hpc-project/tests/stage/$CLUSTER_NAME/*
rm -rf ~/hpc-project/tests/output/$CLUSTER_NAME/*
rm -rf ~/hpc-project/tests/perflogs/$CLUSTER_NAME/*
rm -f ~/hpc-project/reports/osu-benchmark.json

reframe --config-file ulhpc.py --checkpath 4.1-OSU-BENCHMARK-ONESIDE-TEST.py --name 'OSUPlacementTest' --run --report-file=reports/osu-benchmark-$CLUSTER_NAME.json


module load lang/Python/3.11.5-GCCcore-13.2.0

python 4.2-Analyze-Result.py 