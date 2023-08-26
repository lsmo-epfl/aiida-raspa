"""Run RASPA single-component GEMC calculation"""

import sys

import click
import pytest
from aiida.common import NotExistent
from aiida.engine import run, run_get_pk
from aiida.orm import Code, Dict


def example_gemc_single_comp(raspa_code, submit=True):
    """Prepare and submit RASPA calculation with components mixture."""

    # parameters
    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 50,
                "NumberOfInitializationCycles": 50,
                "PrintEvery": 10,
                "Forcefield": "GenericMOFs",
                "EwaldPrecision": 1e-6,
                "CutOff": 12.0,
                "GibbsVolumeChangeProbability": 0.1,
            },
            "System": {
                "box_one": {
                    "type": "Box",
                    "BoxLengths": "25 25 25",
                    "BoxAngles": "90 90 90",
                    "ExternalTemperature": 300.0,
                },
                "box_two": {
                    "type": "Box",
                    "BoxLengths": "25 25 25",
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

    # Contructing builder
    builder = raspa_code.get_builder()
    builder.parameters = parameters
    builder.metadata.options = {
        "resources": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        },
        "max_wallclock_seconds": 1 * 30 * 60,  # 30 min
        "withmpi": False,
    }
    builder.metadata.dry_run = False
    builder.metadata.store_provenance = True

    if submit:
        print("Testing RASPA GEMC with methane ...")
        res, pk = run_get_pk(builder)
        print("calculation pk: ", pk)
        print(
            "Average number of methane molecules/uc (box_one):",
            res["output_parameters"].dict.box_one["components"]["methane"]["loading_absolute_average"],
        )
        print(
            "Average number of methane molecules/uc (box_two):",
            res["output_parameters"].dict.box_two["components"]["methane"]["loading_absolute_average"],
        )
        print("OK, calculation has completed successfully")
        pytest.gemc_single_comp_calc_pk = pk
    else:
        print("Generating test input ...")
        builder.metadata.dry_run = True
        builder.metadata.store_provenance = False
        run(builder)
        print("Submission test successful")
        print("In order to actually submit, add '--submit'")
    print("-----")


@click.command("cli")
@click.argument("codelabel")
@click.option("--submit", is_flag=True, help="Actually submit calculation")
def cli(codelabel, submit):
    """Click interface"""
    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print(f"The code '{codelabel}' does not exist")
        sys.exit(1)
    example_gemc_single_comp(code, submit)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

# EOF
