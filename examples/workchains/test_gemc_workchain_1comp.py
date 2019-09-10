# -*- coding: utf-8 -*-
"""Example to submit one component RaspaGEMCWorkChain"""

from __future__ import absolute_import
from __future__ import print_function
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run
from aiida.plugins import DataFactory
from aiida.orm import Code, Dict, Float, Int
from aiida_raspa.workchains import RaspaGEMCWorkChain

# Data objects
ParameterData = DataFactory('dict')  # pylint: disable=invalid-name


@click.command('cli')
@click.argument('codelabel')
def main(codelabel):
    """Run base workchain"""
    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print("The code '{}' does not exist".format(codelabel))
        sys.exit(1)

    print("Testing RASPA methane GEMC through RaspaGEMCWorkChain ...")

    # parameters
    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 500,
                "NumberOfInitializationCycles": 500,
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

    conv_threshold = Float(0.90)
    additional_cycle = Int(500)

    # Constructing builder
    builder = RaspaGEMCWorkChain.get_builder()
    builder.raspa_base.raspa.code = code  # pylint: disable=no-member
    builder.raspa_base.raspa.parameters = parameters  # pylint: disable=no-member
    builder.raspa_base.raspa.metadata.options = { # pylint: disable=no-member
        "resources": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        },
        "max_wallclock_seconds": 1 * 30 * 60,  # 30 min
        "withmpi": False,
    }
    builder.conv_threshold = conv_threshold
    builder.additional_cycle = additional_cycle

    run(builder)


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

# EOF
