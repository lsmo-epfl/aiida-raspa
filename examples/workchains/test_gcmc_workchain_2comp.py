# -*- coding: utf-8 -*-
"""Example to submit two component RaspaGCMCWorkChain"""

from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run
from aiida.plugins import DataFactory
from aiida.orm import Code, Dict, Float, Int
from aiida_raspa.workchains import RaspaGCMCWorkChain

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

    print("Testing RASPA Xenon:Krypton GCMC through RaspaGCMCWorkChain ...")

    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 400,
                "NumberOfInitializationCycles": 200,
                "PrintEvery": 200,
                "Forcefield": "GenericMOFs",
                "RemoveAtomNumberCodeFromLabel": True,
                "EwaldPrecision": 1e-6,
                "CutOff": 12.0,
            },
            "System": {
                "irmof_1": {
                    "type": "Framework",
                    "UnitCells": "1 1 1",
                    "HeliumVoidFraction": 0.149,
                    "ExternalTemperature": 300.0,
                    "ExternalPressure": 1e5,
                }
            },
            "Component": {
                "krypton": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "SwapProbability": 1.0,
                    "BlockPocketsFileName": {
                        "irmof_1": "irmof_1_krypton",
                    },
                },
                "xenon": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "SwapProbability": 1.0,
                    "BlockPocketsFileName": {
                        "irmof_1": "irmof_1_xenon",
                    },
                },
            },
        })

    # framework
    pwd = os.path.dirname(os.path.realpath(__file__))
    structure = CifData(file=os.path.join(pwd, '../simple_calculations/files', 'IRMOF-1.cif'))
    structure_label = "irmof_1"

    block_pocket_node1 = SinglefileData(
        file=os.path.join(pwd, '../simple_calculations/files', 'IRMOF-1_test.block')).store()
    block_pocket_node2 = SinglefileData(
        file=os.path.join(pwd, '../simple_calculations/files', 'IRMOF-1_test.block')).store()

    conv_threshold = Float(0.10)
    additional_cycle = Int(2000)

    # Constructing builder
    builder = RaspaGCMCWorkChain.get_builder()

    builder.raspa_base.raspa.code = code  # pylint: disable=no-member
    builder.raspa_base.raspa.framework = {  # pylint: disable=no-member
        structure_label: structure,
    }
    builder.raspa_base.raspa.parameters = parameters  # pylint: disable=no-member
    builder.raspa_base.raspa.block_pocket = { # pylint: disable=no-member
        "irmof_1_krypton": block_pocket_node1,
        "irmof_1_xenon": block_pocket_node2,
    }

    builder.raspa_base.raspa.metadata.options = { # pylint: disable=no-member
        "resources": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        },
        "max_wallclock_seconds": 1 * 30 * 60,  # 30 min
        "withmpi": False,
    }

    builder.conv_threshold = conv_threshold
    builder.additional_cycle = additional_cycle

    run(builder)


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

# EOF
