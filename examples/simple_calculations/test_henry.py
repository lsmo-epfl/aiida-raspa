#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Run RASPA calculation to compute Henry coefficient."""
from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run_get_pk, run
from aiida.plugins import DataFactory
from aiida.orm import Code, Dict
from aiida_raspa.calculations import RaspaCalculation  # pylint: disable=unused-import

# data objects
CifData = DataFactory('cif')  # pylint: disable=invalid-name


@click.command('cli')
@click.argument('codelabel')
@click.option('--submit', is_flag=True, help='Actually submit calculation')
def main(codelabel, submit):
    """Prepare and submit simple RASPA calculation to compute Henry coefficient."""
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
                "PrintEvery": 200,
                "Forcefield": "GenericMOFs",
                "EwaldPrecision": 1e-6,
                "CutOff": 12.0,
            },
            "System": {
                "tcc1rs": {
                    "type": "Framework",
                    "UnitCells": "1 1 1",
                    "HeliumVoidFraction": 0.149,
                    "ExternalTemperature": 300.0,
                }
            },
            "Component": {
                "methane": {
                    "MoleculeDefinition": "TraPPE",
                    "WidomProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                }
            },
        })

    # framework
    pwd = os.path.dirname(os.path.realpath(__file__))
    framework = CifData(file=pwd + '/files/TCC1RS.cif')

    # Contructing builder
    builder = code.get_builder()
    builder.framework = {
        "tcc1rs": framework,
    }
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
        print("Testing RASPA on computing Henry coefficient ...")
        res, pk = run_get_pk(builder)
        print("calculation pk: ", pk)
        print("Average Henry coefficient (methane in tcc1rs):",
              res['output_parameters'].dict.tcc1rs['components']['methane']['henry_coefficient_average'])
        print("OK, calculation has completed successfully")
    else:
        print("Generating test input ...")
        builder.metadata.dry_run = True
        builder.metadata.store_provenance = False
        run(builder)
        print("submission test successful")
        print("In order to actually submit, add '--submit'")
    print("-----")


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

# EOF
