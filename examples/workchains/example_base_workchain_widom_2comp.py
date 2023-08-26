"""Two-component Widom insertion through RaspaBaseWorkChain"""

import os
import sys

import click
from aiida.common import NotExistent
from aiida.engine import run_get_node
from aiida.orm import CifData, Code, Dict, SinglefileData

from aiida_raspa.workchains import RaspaBaseWorkChain


def example_base_workchain_widom_2(raspa_code):
    """Run base workchain for widom insertion calculation (1 component)."""

    # pylint: disable=no-member

    print("Testing RASPA Xenon and Krypton widom insertion through RaspaBaseWorkChain ...")

    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 50,
                "PrintEvery": 10,
                "Forcefield": "GenericMOFs",
                "EwaldPrecision": 1e-6,
                "CutOff": 12.0,
            },
            "System": {
                "tcc1rs": {
                    "type": "Framework",
                    "ExternalTemperature": 300.0,
                }
            },
            "Component": {
                "krypton": {
                    "MoleculeDefinition": "TraPPE",
                    "WidomProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                    "BlockPocketsFileName": "block_tcc1rs_methane",
                },
                "xenon": {
                    "MoleculeDefinition": "TraPPE",
                    "WidomProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                    "BlockPocketsFileName": "block_tcc1rs_xenon",
                },
            },
        }
    )

    # framework
    pwd = os.path.dirname(os.path.realpath(__file__))
    structure = CifData(file=os.path.join(pwd, "..", "files", "TCC1RS.cif"))
    structure_label = structure.filename[:-4].lower()

    block_pocket_node1 = SinglefileData(file=os.path.join(pwd, "..", "files", "block_pocket.block")).store()
    block_pocket_node2 = SinglefileData(file=os.path.join(pwd, "..", "files", "block_pocket.block")).store()

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
        "block_tcc1rs_methane": block_pocket_node1,
        "block_tcc1rs_xenon": block_pocket_node2,
    }

    builder.handler_overrides = Dict(
        dict={"check_widom_convergence": True}
    )  # Enable widom convergence handler disabled by default.

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
    example_base_workchain_widom_2(code)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

# EOF
