#!/bin/bash

verdi run /opt/aiida-raspa/examples/simple_calculations/example_base.py --submit raspa
verdi run /opt/aiida-raspa/examples/simple_calculations/example_base_restart.py --previous_calc 4 --submit raspa
verdi run /opt/aiida-raspa/examples/simple_calculations/example_binary_mixture.py --submit raspa
verdi run /opt/aiida-raspa/examples/simple_calculations/example_block_pockets_2frameworks_2molecules.py --submit raspa
verdi run /opt/aiida-raspa/examples/simple_calculations/example_block_pockets_simple.py --submit raspa
