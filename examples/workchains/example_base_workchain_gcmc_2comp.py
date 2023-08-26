"""Two-component GCMC through RaspaBaseWorkChain"""

import os
import sys

import click
from aiida.common import NotExistent
from aiida.engine import run_get_node
from aiida.orm import CifData, Code, Dict, SinglefileData

from aiida_raspa.workchains import RaspaBaseWorkChain


def example_base_workchain_gcmc(raspa_code):
    """Run base workchain for GCMC calculations with 2 components."""

    # pylint: disable=no-member

    print("Testing RASPA Xenon:Krypton GCMC through RaspaBaseWorkChain ...")

    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 50,
                "NumberOfInitializationCycles": 50,
                "PrintEvery": 10,
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
        }
    )

    # framework
    pwd = os.path.dirname(os.path.realpath(__file__))
    structure = CifData(file=os.path.join(pwd, "..", "files", "IRMOF-1.cif"))
    structure_label = "irmof_1"

    block_pocket_node1 = SinglefileData(file=os.path.join(pwd, "..", "files", "IRMOF-1_test.block")).store()
    block_pocket_node2 = SinglefileData(file=os.path.join(pwd, "..", "files", "IRMOF-1_test.block")).store()

    # Constructing builder
    builder = RaspaBaseWorkChain.get_builder()

    # Specifying the code
    builder.raspa.code = raspa_code

    # Specifying the framework
    builder.raspa.framework = {
        structure_label: structure,
    }

    # Specifying the input parameters
    builder.raspa.parameters = parameters

    # Specifying the block pockets
    builder.raspa.block_pocket = {
        "irmof_1_krypton": block_pocket_node1,
        "irmof_1_xenon": block_pocket_node2,
    }

    builder.handler_overrides = Dict(
        dict={"check_gcmc_convergence": True}
    )  # Enable gcmc convergence handler disabled by default.

    # Specifying the scheduler options
    builder.raspa.metadata.options = {
        "resources": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        },
        "max_wallclock_seconds": 1 * 30 * 60,  # 30 min
        "withmpi": False,
    }

    _, node = run_get_node(builder)
    assert node.exit_status == 0


@click.command("cli")
@click.argument("codelabel")
def cli(codelabel):
    """Click interface"""
    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print(f"The code '{codelabel}' does not exist")
        sys.exit(1)
    example_base_workchain_gcmc(code)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

# EOF
