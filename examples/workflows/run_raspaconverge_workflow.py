# -*- coding: utf-8 -*-
"""Example to run base workflows for RASPA"""

from __future__ import absolute_import
from __future__ import print_function
import os
import click

from aiida.common.example_helpers import test_and_get_code  # noqa
from aiida.plugins import DataFactory
from aiida.engine import submit
from aiida_raspa.workflows import RaspaConvergeWorkChain

# Data objects
CifData = DataFactory('cif')  # pylint: disable=invalid-name
ParameterData = DataFactory('parameter')  # pylint: disable=invalid-name
SinglefileData = DataFactory('singlefile')  # pylint: disable=invalid-name


@click.command('cli')
@click.argument('codelabel')
def main(codelabel):
    """Run base workchain"""
    code = test_and_get_code(codelabel, expected_code_type='raspa')

    options_dict = {
        "resources": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        },
        "max_wallclock_seconds": 3 * 60 * 60,
    }

    options = ParameterData(dict=options_dict)

    params_dict = {
        "GeneralSettings": {
            "SimulationType": "MonteCarlo",
            "NumberOfCycles": 2000,
            "NumberOfInitializationCycles": 2000,
            "PrintEvery": 1000,
            "Forcefield": "GenericMOFs",
            "EwaldPrecision": 1e-6,
            "CutOff": 12.0,
            "Framework": 0,
            "UnitCells": "1 1 1",
            "HeliumVoidFraction": 0.149,
            "ExternalTemperature": 300.0,
            "ExternalPressure": 5e5,
        },
        "Component": [{
            "MoleculeName": "methane",
            "MoleculeDefinition": "TraPPE",
            "TranslationProbability": 0.5,
            "ReinsertionProbability": 0.5,
            "SwapProbability": 1.0,
            "CreateNumberOfMolecules": 0,
        }],
    }
    parameters = ParameterData(dict=params_dict)

    # structure
    pwd = os.path.dirname(os.path.realpath(__file__))
    structure = CifData(file=pwd + '/test_raspa_attach_file/TCC1RS.cif')

    submit(
        RaspaConvergeWorkChain,
        code=code,
        structure=structure,
        parameters=parameters,
        options=options,
        _label='MyFirstWokchain',
    )


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

# EOF
