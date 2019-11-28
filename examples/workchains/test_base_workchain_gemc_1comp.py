# -*- coding: utf-8 -*-
"""One-component GEMC through RaspaBaseWorkChain"""

from __future__ import absolute_import
from __future__ import print_function
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run
from aiida.orm import Code, Dict
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

    print("Testing RASPA methane GEMC through RaspaBaseWorkChain ...")

    # parameters
    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 200,
                "NumberOfInitializationCycles": 200,
                "PrintEvery": 100,
                "Forcefield": "GenericMOFs",
                "CutOff": 12.0,
                "GibbsVolumeChangeProbability": 0.1,
            },
            "System": {
                "box_one": {
                    "type": "Box",
                    "BoxLengths": "30 30 30",
                    "BoxAngles": "90 90 90",
                    "ExternalTemperature": 300.0,
                },
                "box_two": {
                    "type": "Box",
                    "BoxLengths": "30 30 30",
                    "BoxAngles": "90 90 90",
                    "ExternalTemperature": 300.0,
                }
            },
            "Component": {
                "methane": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 1.0,
                    "ReinsertionProbability": 1.0,
                    "GibbsSwapProbability": 1.0,
                    "CreateNumberOfMolecules": {
                        "box_one": 150,
                        "box_two": 150,
                    },
                },
            },
        })

    # Constructing builder
    builder = RaspaBaseWorkChain.get_builder()

    # Specifying the code
    builder.raspa.code = code

    # Specifying the input parameters
    builder.raspa.parameters = parameters

    # Add fixers that could handle physics-related problems.
    builder.fixers = {
        'fixer_001': ('aiida_raspa.utils', 'check_gemc_box'),
        'fixer_002': ('aiida_raspa.utils', 'check_gemc_convergence', 0.8, 200, 200),
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
