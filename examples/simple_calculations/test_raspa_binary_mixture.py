#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Run RASPA calculation with components mixture."""

from __future__ import print_function
from __future__ import absolute_import
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run
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
                "NumberOfCycles": 2000,
                "NumberOfInitializationCycles": 2000,
                "PrintEvery": 1000,
                "Forcefield": "GenericMOFs",
                "EwaldPrecision": 1e-6,
                "CutOff": 12.0,
                "ExternalTemperature": 300.0,
                "ExternalPressure": 5e5,
            },
            "System": {
                "box0": {
                    "type": "Box",
                    "BoxLengths": "25 25 25",
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
        run(RaspaCalculation, **inputs)
        #print(("submitted calculation; calc=Calculation(uuid='{}') # ID={}"\
        #        .format(calc.uuid,calc.dbnode.pk)))
    else:
        inputs["metadata"]["dry_run"] = True
        inputs["metadata"]["store_provenance"] = False
        run(RaspaCalculation, **inputs)
        print("submission test successful")
        print("In order to actually submit, add '--submit'")


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

# EOF
