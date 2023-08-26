"""Example for RaspaBaseWorkChain."""

import os
import sys

import click
from aiida.common import NotExistent
from aiida.engine import run_get_node
from aiida.orm import CifData, Code, Dict, Int, SinglefileData

from aiida_raspa.workchains import RaspaBaseWorkChain


def example_base_restart_timeout(raspa_code):
    """Run base workchain for GCMC with restart after timeout."""

    # pylint: disable=no-member

    print("Testing RaspaBaseWorkChain restart after timeout...")
    print("This long simulation will require ca. 3 iterations (i.e., 2 restarts).")

    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfInitializationCycles": 5000,  # many, to pass timeout
                "NumberOfCycles": 5000,  # many, to pass timeout
                "PrintEvery": 1000,
                "Forcefield": "GenericMOFs",
                "RemoveAtomNumberCodeFromLabel": True,
                "ChargeMethod": "None",
                "CutOff": 12.0,
                # WriteBinaryRestartFileEvery not needed: if missing RaspaBaseWorkChain will assign a default of 1000
            },
            "System": {
                "irmof_1": {
                    "type": "Framework",
                    "UnitCells": "1 1 1",
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
            },
        }
    )

    # framework
    pwd = os.path.dirname(os.path.realpath(__file__))
    structure = CifData(file=os.path.join(pwd, "..", "files", "IRMOF-1.cif"))
    structure_label = "irmof_1"

    block_pocket_node1 = SinglefileData(file=os.path.join(pwd, "..", "files", "IRMOF-1_test.block")).store()

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
    }

    # Specifying the scheduler options
    builder.raspa.metadata.options = {
        "resources": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        },
        "max_wallclock_seconds": 1 * 30 * 60,  # 30 min
        "withmpi": True,  # A trick to put the kill below before raspa command.
        "mpirun_extra_params": ["timeout", "5"],  # Kill the calculation after 5 seconds, to test restart.
    }

    # Specify RaspaBaseWorkChain options
    builder.max_iterations = Int(8)  # number of maximum iterations: prevent for infinite restart (default: 5)

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
    example_base_restart_timeout(code)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

# EOF
