#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Restart from simple RASPA calculation."""

from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run
from aiida.orm import Code, Dict, load_node
from aiida.plugins import DataFactory
from aiida_raspa.calculations import RaspaCalculation

# data objects
CifData = DataFactory('cif')  # pylint: disable=invalid-name


@click.command('cli')
@click.argument('codelabel')
@click.option('--previous_calc', '-p', required=True, type=int, help='PK of test_raspa_base.py calculation')
@click.option('--submit', is_flag=True, help='Actually submit calculation')
def main(codelabel, previous_calc, submit):
    """Prepare and submit restart from simple RASPA calculation."""
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
                "HeliumVoidFraction": 0.149,
                "ExternalTemperature": 300.0,
                "ExternalPressure": 5e5,
            },
            "System": {
                "tcc1rs": {
                    "type": "Framework",
                    "UnitCells": "1 1 1"
                },
            },
            "Component": {
                "methane": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                }
            },
        })

    # framework
    pwd = os.path.dirname(os.path.realpath(__file__))
    framework = CifData(file=pwd + '/test_raspa_attach_file/TCC1RS.cif')

    # restart file
    retrieved_parent_folder = load_node(previous_calc).outputs.retrieved

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
        "retrieved_parent_folder": retrieved_parent_folder,
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
