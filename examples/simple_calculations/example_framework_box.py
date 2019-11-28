#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Run simple RASPA calculation."""

from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import click
import pytest

from aiida.common import NotExistent
from aiida.engine import run_get_pk, run
from aiida.orm import Code, Dict
from aiida.plugins import DataFactory

# data objects
CifData = DataFactory('cif')  # pylint: disable=invalid-name


def example_framework_box(raspa_code, submit=True):
    """"Test RASPA with framework and box."""

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

    pwd = os.path.dirname(os.path.realpath(__file__))
    # framework
    framework = CifData(file=os.path.join(pwd, '..', 'files', 'TCC1RS.cif'))

    # Contructing builder
    builder = raspa_code.get_builder()
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
        print("Testing RASPA with framework and box ...")
        res, pk = run_get_pk(builder)
        print("calculation pk: ", pk)
        print("Total Energy average (tcc1rs):", res['output_parameters'].dict.tcc1rs['general']['total_energy_average'])
        print("Total Energy average (box_25_angstroms):",
              res['output_parameters'].dict.box_25_angstroms['general']['total_energy_average'])
        print("OK, calculation has completed successfully")
        pytest.framework_box_calc_pk = pk
    else:
        print("Generating test input ...")
        builder.metadata.dry_run = True
        builder.metadata.store_provenance = False
        run(builder)
        print("Submission test successful")
        print("In order to actually submit, add '--submit'")
    print("-----")


@click.command('cli')
@click.argument('codelabel')
@click.option('--submit', is_flag=True, help='Actually submit calculation')
def cli(codelabel, submit):
    """Click interface"""
    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print("The code '{}' does not exist".format(codelabel))
        sys.exit(1)
    example_framework_box(code, submit)


if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter

# EOF
