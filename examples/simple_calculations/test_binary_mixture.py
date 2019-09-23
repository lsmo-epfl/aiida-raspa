# -*- coding: utf-8 -*-
"""Run RASPA calculation with components mixture."""

from __future__ import print_function
from __future__ import absolute_import
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run_get_pk, run
from aiida.orm import Code, Dict


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
            },
            "System": {
                "box_25_angstrom": {
                    "type": "Box",
                    "BoxLengths": "25 25 25",
                    "ExternalTemperature": 300.0,
                    "ExternalPressure": 5e5,
                },
            },
            "Component": {
                "propane": {
                    "MoleculeName": "propane",
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 1.0,
                    "ReinsertionProbability": 1.0,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": 30,
                },
                "butane": {
                    "MoleculeName": "butane",
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 1.0,
                    "ReinsertionProbability": 1.0,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": 30,
                },
            },
        })

    # Contructing builder
    builder = code.get_builder()
    builder.parameters = parameters
    builder.metadata.options = {
        "resources": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        },
        "max_wallclock_seconds": 1 * 30 * 60,  # 30 min
        "withmpi": False,
    }
    builder.metadata.dry_run = False
    builder.metadata.store_provenance = True

    if submit:
        print("Testing RASPA with binary mixture (propane/butane) ...")
        res, pk = run_get_pk(builder)
        print("calculation pk: ", pk)
        print("Total Energy average (box_25_angstrom):",
              res['output_parameters'].dict.box_25_angstrom['general']['total_energy_average'])
        print("OK, calculation has completed successfully")
    else:
        print("Generating test input ...")
        builder.metadata.dry_run = True
        builder.metadata.store_provenance = False
        run(builder)
        print("Submission test successful")
        print("In order to actually submit, add '--submit'")
    print("-----")


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

# EOF
