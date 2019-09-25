# -*- coding: utf-8 -*-
"""Two-component GCMC through RaspaBaseWorkChain"""

from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run
from aiida.orm import CifData, Code, Dict, SinglefileData
from aiida_raspa.workchains import RaspaBaseWorkChain


@click.command('cli')
@click.argument('codelabel')
def main(codelabel):
    """Run base workchain"""

    # pylint: disable=no-member

    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print("The code '{}' does not exist".format(codelabel))
        sys.exit(1)

    print("Testing RASPA Xenon:Krypton GCMC through RaspaBaseWorkChain ...")

    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 2000,
                "NumberOfInitializationCycles": 2000,
                "PrintEvery": 200,
                "Forcefield": "GenericMOFs",
                "RemoveAtomNumberCodeFromLabel": True,
                "EwaldPrecision": 1e-6,
                "CutOff": 12.0,
            },
            "System": {
                "irmof_1": {
                    "type": "Framework",
                    "UnitCells": "1 1 1",
                    "HeliumVoidFraction": 0.149,
                    "ExternalTemperature": 300.0,
                    "ExternalPressure": 1e5,
                }
            },
            "Component": {
                "krypton": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "SwapProbability": 1.0,
                    "BlockPocketsFileName": {
                        "irmof_1": "irmof_1_krypton",
                    },
                },
                "xenon": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "SwapProbability": 1.0,
                    "BlockPocketsFileName": {
                        "irmof_1": "irmof_1_xenon",
                    },
                },
            },
        })

    # framework
    pwd = os.path.dirname(os.path.realpath(__file__))
    structure = CifData(file=os.path.join(pwd, '..', 'simple_calculations', 'files', 'IRMOF-1.cif'))
    structure_label = "irmof_1"

    block_pocket_node1 = SinglefileData(
        file=os.path.join(pwd, '..', 'simple_calculations', 'files', 'IRMOF-1_test.block')).store()
    block_pocket_node2 = SinglefileData(
        file=os.path.join(pwd, '..', 'simple_calculations', 'files', 'IRMOF-1_test.block')).store()

    # Constructing builder
    builder = RaspaBaseWorkChain.get_builder()

    # Specifying the code
    builder.raspa.code = code

    # Specifying the framework
    builder.raspa.framework = {
        structure_label: structure,
    }

    # Specifying the input parameters
    builder.raspa.parameters = parameters

    # Specifying the block pockets
    builder.raspa.block_pocket = {
        "irmof_1_krypton": block_pocket_node1,
        "irmof_1_xenon": block_pocket_node2,
    }

    # Add fixtures that could handle physics-related problems.
    builder.fixtures = {
        'fixture_001': ('aiida_raspa.utils', 'check_gcmc_convergence', 0.10, 2000, 2000),
    }

    # Specifying the scheduler options
    builder.raspa.metadata.options = {
        "resources": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        },
        "max_wallclock_seconds": 1 * 30 * 60,  # 30 min
        "withmpi": False,
    }

    run(builder)


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

# EOF
