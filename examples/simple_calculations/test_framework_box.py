#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Run simple RASPA calculation."""

from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run_get_pk, run
from aiida.orm import Code, Dict
from aiida.plugins import DataFactory
from aiida_raspa.calculations import RaspaCalculation

# data objects
CifData = DataFactory('cif')  # pylint: disable=invalid-name


@click.command('cli')
@click.argument('codelabel')
@click.option('--submit', is_flag=True, help='Actually submit calculation')
def main(codelabel, submit):
    """Prepare and submit simple RASPA calculation."""
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
                "PrintEvery": 100,
                "Forcefield": "GenericMOFs",
                "EwaldPrecision": 1e-6,
                "WriteBinaryRestartFileEvery": 200,
            },
            "System": {
                "tcc1rs": {
                    "type": "Framework",
                    "UnitCells": "1 1 1",
                    "ExternalTemperature": 300.0,
                    "ExternalPressure": 5e5,
                    "HeliumVoidFraction": 0.149,
                },
                "box_25_angstroms": {
                    "type": "Box",
                    "BoxLengths": "25 25 25",
                    "ExternalTemperature": 300.0,
                    "ExternalPressure": 5e5,
                },
            },
            "Component": {
                "methane": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": {
                        "tcc1rs": 1,
                        "box_25_angstroms": 2,
                    }
                }
            },
        })

    # framework
    framework = CifData(file=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'files', 'TCC1RS.cif'))

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
            "tcc1rs": framework,
        },
        "parameters": parameters,
        "code": code,
        "metadata": {
            "options": options,
            "dry_run": False,
            "store_provenance": True,
        }
    }

    if submit:
        print("Testing RASPA with framework and box ...")
        res, pk = run_get_pk(RaspaCalculation, **inputs)
        print("calculation pk: ", pk)
        print("Total Energy average (tcc1rs):", res['output_parameters'].dict.tcc1rs['general']['total_energy_average'])
        print("Total Energy average (box_25_angstroms):",
              res['output_parameters'].dict.box_25_angstroms['general']['total_energy_average'])
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
