#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Run simple RASPA calculation."""

from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run
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
                "NumberOfCycles": 600,
                "NumberOfInitializationCycles": 0,
                "PrintEvery": 100,
                "ChargeMethod": "Ewald",
                "Forcefield": "GenericMOFs",
                "EwaldPrecision": 1e-6,
                "CutOff": 12.0,
                "HeliumVoidFraction": 0.149,
                "WriteBinaryRestartFileEvery": 200,
            },
            "System": {
                "cu_btc": {
                    "type": "Framework",
                    "UnitCells": "1 1 1",
                    "ExternalTemperature": 300.0,
                    "ExternalPressure": 5e5,
                },
            },
            "Component": {
                "CO2": {
                    "MoleculeDefinition": "TraPPE",
                    "MolFraction": 0.15,
                    "IdealGasRosenbluthWeight": 1.0,
                    "TranslationProbability": 0.5,
                    "RotationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "CBMCProbability": 0.5,
                    "IdentityChangeProbability": 1.0,
                    "IdentityChangeList": [0, 1, 2],
                    "NumberOfIdentityChanges": 2,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                },
                "methane": {
                    "MoleculeDefinition": "TraPPE",
                    "MolFraction": 0.1,
                    "IdealGasRosenbluthWeight": 1.0,
                    "TranslationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "CBMCProbability": 0.5,
                    "IdentityChangeProbability": 1.0,
                    "IdentityChangeList": [0, 1, 2],
                    "NumberOfIdentityChanges": 2,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                },
                "N2": {
                    "MoleculeDefinition": "TraPPE",
                    "MolFraction": 0.1,
                    "IdealGasRosenbluthWeight": 1.0,
                    "TranslationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "CBMCProbability": 0.5,
                    "IdentityChangeProbability": 1.0,
                    "IdentityChangeList": [0, 1, 2],
                    "NumberOfIdentityChanges": 2,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                },
            },
        })

    # framework
    pwd = os.path.dirname(os.path.realpath(__file__))
    framework = CifData(file=pwd + '/test_raspa_attach_file/Cu-BTC.cif')

    # resources
    options = {
        "resources": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        },
        "max_wallclock_seconds": 1 * 30 * 60,  # 30 min
    }

    # collecting all the inputs
    inputs = {
        "framework": {
            "cu_btc": framework,
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
