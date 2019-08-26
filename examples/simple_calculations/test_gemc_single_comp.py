# -*- coding: utf-8 -*-
"""Run RASPA single-component GEMC calculation"""

from __future__ import print_function
from __future__ import absolute_import
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run_get_pk, run
from aiida.orm import Code, Dict
from aiida_raspa.calculations import RaspaCalculation


@click.command('cli')
@click.argument('codelabel')
@click.option('--submit', is_flag=True, help='Actually submit calculation')
def main(codelabel, submit):
    """Prepare and submit RASPA calculation with components mixture."""
    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print("The code '{}' does not exist".format(codelabel))
        sys.exit(1)

    # parameters
    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 400,
                "NumberOfInitializationCycles": 200,
                "PrintEvery": 200,
                "Forcefield": "GenericMOFs",
                "EwaldPrecision": 1e-6,
                "CutOff": 12.0,
                "GibbsVolumeChangeProbability": 0.1,
            },
            "System": {
                "box_one": {
                    "type": "Box",
                    "BoxLengths": "25 25 25",
                    "BoxAngles": "90 90 90",
                    "ExternalTemperature": 300.0,
                },
                "box_two": {
                    "type": "Box",
                    "BoxLengths": "25 25 25",
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

    # resources
    options = {
        "resources": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        },
        "max_wallclock_seconds": 1 * 30 * 60,  # 30 min
        "withmpi": False,
    }

    # collecting all the inputs
    inputs = {
        "parameters": parameters,
        "code": code,
        "metadata": {
            "options": options,
            "dry_run": False,
            "store_provenance": True,
        }
    }

    if submit:
        print("Testing RASPA GEMC with methane ...")
        res, pk = run_get_pk(RaspaCalculation, **inputs)
        print("calculation pk: ", pk)
        print("Total Energy average (box_one):",
              res['output_parameters'].dict.box_one['general']['total_energy_average'])
        print("Total Energy average (box_two):",
              res['output_parameters'].dict.box_two['general']['total_energy_average'])
        print("OK, calculation has completed successfully")
    else:
        print("Generating test input ...")
        inputs["metadata"]["dry_run"] = True
        inputs["metadata"]["store_provenance"] = False
        run(RaspaCalculation, **inputs)
        print("Submission test successful")
        print("In order to actually submit, add '--submit'")
    print("-----")


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

# EOF
