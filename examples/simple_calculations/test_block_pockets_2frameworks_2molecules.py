# -*- coding: utf-8 -*-
"""Run RASPA calculation with blocked pockets."""
from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run_get_pk, run
from aiida.orm import Code, Dict, SinglefileData
from aiida.plugins import DataFactory
from aiida_raspa.calculations import RaspaCalculation

# data objects
CifData = DataFactory('cif')  # pylint: disable=invalid-name


@click.command('cli')
@click.argument('codelabel')
@click.option('--submit', is_flag=True, help='Actually submit calculation')
def main(codelabel, submit):
    """Prepare and submit RASPA calculation with blocked pockets."""
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
                },
                "irmof_10": {
                    "type": "Framework",
                    "UnitCells": "1 1 1",
                    "HeliumVoidFraction": 0.149,
                    "ExternalTemperature": 300.0,
                    "ExternalPressure": 1e5,
                }
            },
            "Component": {
                "methane": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": {
                        "irmof_1": 1,
                        "irmof_10": 2,
                    },
                    "BlockPocketsFileName": {
                        "irmof_1": "irmof_1_4",
                        "irmof_10": "irmof_1_5",
                    },
                },
                "xenon": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": {
                        "irmof_1": 3,
                        "irmof_10": 4,
                    },
                    "BlockPocketsFileName": {
                        "irmof_1": "irmof_1_5",
                        "irmof_10": "irmof_1_4",
                    },
                },
            },
        })

    # frameworks
    pwd = os.path.dirname(os.path.realpath(__file__))
    framework_1 = CifData(file=os.path.join(pwd, 'files', 'IRMOF-1.cif'))
    framework_10 = CifData(file=os.path.join(pwd, 'files', 'IRMOF-10.cif'))

    # block pocket
    block_pocket_1_4 = SinglefileData(file=os.path.join(pwd, 'files', 'IRMOF-1-4.block')).store()
    block_pocket_1_5 = SinglefileData(file=os.path.join(pwd, 'files', 'IRMOF-1-5.block')).store()

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
        "framework": {
            "irmof_1": framework_1,
            "irmof_10": framework_10,
        },
        "parameters": parameters,
        "block_pocket": {
            "irmof_1_4": block_pocket_1_4,
            "irmof_1_5": block_pocket_1_5,
        },
        "code": code,
        "metadata": {
            "options": options,
            "dry_run": False,
            "store_provenance": True,
        }
    }

    if submit:
        print("Testing RASPA calculation with two frameworks each one "
              "containing 2 molecules (metahne/xenon) and bock pockets ...")
        res, pk = run_get_pk(RaspaCalculation, **inputs)
        print("calculation pk: ", pk)
        print("Total Energy average (irmof_1):",
              res['output_parameters'].dict.irmof_1['general']['total_energy_average'])
        print("Total Energy average (irmof_10):",
              res['output_parameters'].dict.irmof_10['general']['total_energy_average'])
        print("OK, calculation has completed successfully")
    else:
        print("Generating test input ...")
        inputs["metadata"]["dry_run"] = True
        inputs["metadata"]["store_provenance"] = False
        run(RaspaCalculation, **inputs)
        print("Submission test successful")
        print("In order to actually submit, add '--submit'")


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

# EOF
