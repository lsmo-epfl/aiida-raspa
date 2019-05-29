#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
import os
import click

from aiida.common.example_helpers import test_and_get_code
from aiida.orm import DataFactory

# data objects
CifData = DataFactory('cif')
ParameterData = DataFactory('parameter')
SinglefileData = DataFactory('singlefile')


@click.command('cli')
@click.argument('codelabel')
@click.option('--submit', is_flag=True, help='Actually submit calculation')
def main(codelabel, submit):
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
                "Box": 0,
                "BoxLengths": "25 25 25",
                "ExternalTemperature": 300.0,
                "ExternalPressure": 5e5,
            },
            "Component": [{
                "MoleculeName": "propane",
                "MoleculeDefinition": "TraPPE",
                "TranslationProbability": 1.0,
                "ReinsertionProbability": 1.0,
                "SwapProbability": 1.0,
                "CreateNumberOfMolecules": 30,
            }, {
                "MoleculeName": "butane",
                "MoleculeDefinition": "TraPPE",
                "TranslationProbability": 1.0,
                "ReinsertionProbability": 1.0,
                "SwapProbability": 1.0,
                "CreateNumberOfMolecules": 30,
            }],
        })
    calc.use_parameters(parameters)

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
