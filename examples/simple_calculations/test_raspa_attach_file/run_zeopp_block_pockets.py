#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
import os
import click


@click.command('cli')
@click.argument('codelabel')
@click.option('--submit', is_flag=True, help='Actually submit calculation')
def main(codelabel, submit):
    """Command line interface for testing and submitting calculations.

    This script extends submit.py, adding flexibility in the selected code/computer.

    Run './cli.py --help' to see options.
    """
    code = Code.get_from_string(codelabel)

    # set up calculation
    calc = code.new_calc()
    calc.label = "aiida_zeopp example calculation"
    calc.description = "Converts .cif to .cssr format, computes surface area, pore volume and channels"
    calc.set_max_wallclock_seconds(30 * 60)
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1})

    # Prepare input parameters
    NetworkParameters = DataFactory('zeopp.parameters')
    d = {
        'cssr': True,
        'sa': [1.82, 1.82, 1000],
        'volpo': [1.82, 1.82, 1000],
        'chan': 1.2,
        'ha': True,
        'block': [1.82, 1000],
    }
    parameters = NetworkParameters(dict=d)
    calc.use_parameters(parameters)

    CifData = DataFactory('cif')
    this_dir = os.path.dirname(os.path.realpath(__file__))
    structure = CifData(file=os.path.join(this_dir, 'TCC1RS.cif'))
    calc.use_structure(structure)

    if submit:
        calc.store_all()
        calc.submit()
        print("submitted calculation; calc=Calculation(uuid='{}') # ID={}"\
                .format(calc.uuid,calc.dbnode.pk))
    else:
        subfolder, script_filename = calc.submit_test()
        path = os.path.relpath(subfolder.abspath)
        print("submission test successful")
        print("Find remote folder in {}".format(path))
        print("In order to actually submit, add '--submit'")


if __name__ == '__main__':
    main()
