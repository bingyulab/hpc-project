site_configuration = {  
    'systems': [  
        {  
            'name': 'aion',  
            'descr': 'Aion cluster',  
            'hostnames': [r'aion-\d{4}'],  
            'modules_system': 'lmod',  
            'partitions': [  
                {  
                    'name': 'batch',  
                    'descr': 'Aion compute nodes',  
                    'scheduler': 'slurm',  
                    'launcher': 'srun',  
                    'access': ['--partition=batch', '--qos=normal'],  
                    'max_jobs': 8,  
                    'environs': ['testing-foss'],  
                }  
            ]  
        },  
        {  
            'name': 'iris',  
            'descr': 'Iris cluster',  
            'hostnames': [r'iris-\d{3}'],  
            'modules_system': 'lmod',  
            'partitions': [  
                {  
                    'name': 'batch',  
                    'descr': 'Iris compute nodes',  
                    'scheduler': 'slurm',  
                    'launcher': 'srun',  
                    'access': ['--partition=batch', '--qos=normal'],  
                    'max_jobs': 8,  
                    'environs': ['testing-foss'],  
                }  
            ]  
        }  
    ],  
    'environments': [  
        {
            'name': 'testing',
            'modules': ['env/testing/2023b'],
            'cc': 'gcc',
            'cxx': 'g++',
            'ftn': 'gfortran',
            'target_systems': ['aion', 'iris']
        },
        {  
            'name': 'foss',  
            'modules': ['toolchain/foss/2023b'],  
            'cc': 'gcc',  
            'cxx': 'g++',  
            'ftn': 'gfortran',  
            'target_systems': ['aion', 'iris']  
        }, 
        {
            'name': 'testing-foss',
            # Load testing first, then foss (order matters for module dependencies)
            'modules': ['env/testing/2023b', 'toolchain/foss/2023b'],
            'cc': 'gcc',
            'cxx': 'g++',
            'ftn': 'gfortran',
            'target_systems': ['aion', 'iris']
        },
        {  
            'name': 'system-gcc',  
            'cc': 'gcc',  
            'cxx': 'g++',  
            'ftn': 'gfortran',  
            'target_systems': ['aion', 'iris']  
        },  
    ],
    'general': [
        {
            'report_file': './reports/report-{sessionid}.json',  # Report file pattern
            'keep_stage_files': False,                    # Don't keep stage files
            'purge_environment': True,                    # Clean environment between tests
        }
    ]  
}  
