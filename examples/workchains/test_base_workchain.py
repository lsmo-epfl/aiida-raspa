# -*- coding: utf-8 -*-
"""Example to run RaspaBaseWorkChain - Widom Particle Insertion"""

from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run
from aiida.plugins import DataFactory
from aiida.orm import Code, Dict
from aiida_raspa.workchains import RaspaBaseWorkChain

# Data objects
CifData = DataFactory('cif')  # pylint: disable=invalid-name
ParameterData = DataFactory('dict')  # pylint: disable=invalid-name
SinglefileData = DataFactory('singlefile')  # pylint: disable=invalid-name


@click.command('cli')
@click.argument('codelabel')
def main(codelabel):
    """Run base workchain"""
    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print("The code '{}' does not exist".format(codelabel))
        sys.exit(1)

    print("Testing RASPA methane adsorption through RaspaBaseWorkChain ...")

    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 1000,
                "NumberOfInitializationCycles": 1000,
                "PrintEvery": 200,
                "Forcefield": "GenericMOFs",
                "CutOff": 12.0,
                "WriteBinaryRestartFileEvery": 200,
            },
            "System": {
                "tcc1rs": {
                    "type": "Framework",
                    "UnitCells": "1 1 1",
                    "HeliumVoidFraction": 0.149,
                    "ExternalTemperature": 300.0,
                    "ExternalPressure": 1e5,
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
    framework = CifData(
        file=os.path.join(os.path.dirname(os.path.realpath(__file__)), '../simple_calculations/files', 'TCC1RS.cif'))

    # Constructing builder
    builder = RaspaBaseWorkChain.get_builder()
    builder.raspa.code = code  # pylint: disable=no-member
    builder.raspa.framework = {"tcc1rs": framework}  # pylint: disable=no-member
    builder.raspa.parameters = parameters  # pylint: disable=no-member
    builder.raspa.metadata.options.resources = { # pylint: disable=no-member
        "num_machines": 1,
        "num_mpiprocs_per_machine": 1,
    }
    builder.raspa.metadata.options.max_wallclock_seconds = 1 * 30 * 60  # pylint: disable=no-member
    builder.raspa.metadata.options.withmpi = False  # pylint: disable=no-member

    run(builder)


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

# EOF
