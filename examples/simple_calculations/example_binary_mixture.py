"""Run RASPA calculation with components mixture."""

import sys

import click
from aiida.common import NotExistent
from aiida.engine import run, run_get_pk
from aiida.orm import Code, Dict


def example_binary_misture(raspa_code, submit=True):
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
            },
            "System": {
                "box_25_angstrom": {
                    "type": "Box",
                    "BoxLengths": "25 25 25",
                    "ExternalTemperature": 300.0,
                    "ExternalPressure": 5e5,
                },
            },
            "Component": {
                "propane": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 1.0,
                    "RotationProbability": 1.0,
                    "ReinsertionProbability": 1.0,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": 30,
                },
                "butane": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 1.0,
                    "RotationProbability": 1.0,
                    "ReinsertionProbability": 1.0,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": 30,
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
        print("Testing RASPA with binary mixture (propane/butane) ...")
        res, pk = run_get_pk(builder)
        print("calculation pk: ", pk)
        print(
            "Average number of propane molecules/uc:",
            res["output_parameters"].dict.box_25_angstrom["components"]["propane"]["loading_absolute_average"],
        )
        print("OK, calculation has completed successfully")
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
    example_binary_misture(code, submit)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

# EOF
