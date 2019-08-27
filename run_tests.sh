#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

# Run precommit
pre-commit run --all-files || ( git status --short ; git diff ; exit 1 )

# Run pytest
pytest 

# run single calculation tests
verdi run examples/simple_calculations/test_base.py                                 raspa --submit | tee test_output.txt
	pk_base=`cat test_output.txt | grep "calculation pk:" | awk '{print $3}'`
verdi run examples/simple_calculations/test_binary_restart.py                       raspa --submit --previous_calc ${pk_base}
verdi run examples/simple_calculations/test_restart.py                              raspa --submit --previous_calc ${pk_base}
verdi run examples/simple_calculations/test_binary_mixture.py                       raspa --submit
verdi run examples/simple_calculations/test_henry.py                                raspa --submit
verdi run examples/simple_calculations/test_identity.py                             raspa --submit
verdi run examples/simple_calculations/test_block_pockets_simple.py                 raspa --submit
verdi run examples/simple_calculations/test_framework_box.py                        raspa --submit | tee test_output.txt
	pk_framework_box=`cat test_output.txt | grep "calculation pk:" | awk '{print $3}'`
verdi run examples/simple_calculations/test_framework_box_restart.py                raspa --submit --previous_calc ${pk_framework_box}
verdi run examples/simple_calculations/test_block_pockets_2frameworks_2molecules.py raspa --submit
verdi run examples/simple_calculations/test_gemc_single_comp.py raspa --submit | tee test_output.txt
	pk_gemc=`cat test_output.txt | grep "calculation pk:" | awk '{print $3}'`
verdi run examples/simple_calculations/test_gemc_single_comp_restart.py raspa --submit --previous_calc ${pk_gemc}

# run workchains

# if all tests ran successfully
echo "All tests have passed :-)"
