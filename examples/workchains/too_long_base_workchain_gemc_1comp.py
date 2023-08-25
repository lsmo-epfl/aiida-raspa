"""One-component GEMC through RaspaBaseWorkChain"""

import sys

import click
from aiida.common import NotExistent
from aiida.engine import run_get_node
from aiida.orm import Code, Dict

from aiida_raspa.workchains import RaspaBaseWorkChain


def example_base_workchain_gemc(raspa_code):
    """Run the base workchain for GEMC calculation."""

    # pylint: disable=no-member

    print("Testing RASPA methane GEMC through RaspaBaseWorkChain ...")

    # parameters
    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 50,
                "NumberOfInitializationCycles": 50,
                "PrintEvery": 10,
                "Forcefield": "GenericMOFs",
                "CutOff": 12.0,
                "GibbsVolumeChangeProbability": 0.1,
            },
            "System": {
                "box_one": {
                    "type": "Box",
                    "BoxLengths": "30 30 30",
                    "BoxAngles": "90 90 90",
                    "ExternalTemperature": 300.0,
                },
                "box_two": {
                    "type": "Box",
                    "BoxLengths": "30 30 30",
                    "BoxAngles": "90 90 90",
                    "ExternalTemperature": 300.0,
                },
            },
            "Component": {
                "methane": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 1.0,
                    "ReinsertionProbability": 1.0,
                    "GibbsSwapProbability": 1.0,
                    "CreateNumberOfMolecules": {
                        "box_one": 150,
                        "box_two": 150,
                    },
                },
            },
        }
    )

    # Constructing builder
    builder = RaspaBaseWorkChain.get_builder()

    # Specifying the code
    builder.raspa.code = raspa_code

    # Specifying the input parameters
    builder.raspa.parameters = parameters

    # Add handlers that could handle physics-related problems.
    builder.handler_overrides = Dict(
        dict={
            "check_gemc_box": True,
            "check_gemc_convergence": True,
        }
    )  # Enable gemc handlers disabled by default.

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
    example_base_workchain_gemc(code)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

# EOF
