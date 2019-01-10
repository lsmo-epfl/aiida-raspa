#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
import os
import click

from aiida.common.example_helpers import test_and_get_code
from aiida.orm import load_node, DataFactory

# data objects
CifData = DataFactory('cif')
ParameterData = DataFactory('parameter')
SinglefileData = DataFactory('singlefile')


@click.command('cli')
@click.argument('codelabel')
@click.option(
    '--block_pockets',
    '-b',
    required=True,
    type=int,
    help='Block pockets node, can be updained using'
    ' test_raspa_attach_file/run_zeopp_block_pockets.py')
@click.option('--submit', is_flag=True, help='Actually submit calculation')
def main(codelabel, block_pockets, submit):
    code = test_and_get_code(codelabel, expected_code_type='raspa')

    # calc object
    calc = code.new_calc()

    # parameters
    parameters = ParameterData(
        dict={
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
        })
    calc.use_parameters(parameters)

    # structure
    pwd = os.path.dirname(os.path.realpath(__file__))
    framework = CifData(file=pwd + '/test_raspa_attach_file/TCC1RS.cif')
    calc.use_structure(framework)

    # block pockets
    bp = load_node(block_pockets)
    calc.use_block_component_0(bp)

    # resources
    calc.set_max_wallclock_seconds(30 * 60)  # 30 min
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})
    calc.set_withmpi(False)
    #calc.set_queue_name("serial")

    if submit:
        calc.store_all()
        calc.submit()
        print(("submitted calculation; calc=Calculation(uuid='{}') # ID={}"\
                .format(calc.uuid,calc.dbnode.pk)))
    else:
        subfolder = calc.submit_test()[0]
        path = os.path.relpath(subfolder.abspath)
        print("submission test successful")
        print(("Find remote folder in {}".format(path)))
        print("In order to actually submit, add '--submit'")


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

# EOF
