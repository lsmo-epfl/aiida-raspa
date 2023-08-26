"""Restart from simple RASPA calculation."""

import os
import sys

import click
import pytest
from aiida.common import NotExistent
from aiida.engine import run, run_get_pk
from aiida.orm import Code, Dict, load_node
from aiida.plugins import DataFactory

# data objects
CifData = DataFactory("cif")  # pylint: disable=invalid-name


def example_binary_restart(raspa_code, base_calc_pk=None, submit=True):
    """Prepare and submit restart from simple RASPA calculation."""

    # This line is needed for tests only
    if base_calc_pk is None:
        base_calc_pk = pytest.base_calc_pk  # pylint: disable=no-member

    # parameters
    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 400,
                "NumberOfInitializationCycles": 200,
                "PrintEvery": 200,
                "Forcefield": "GenericMOFs",
                "EwaldPrecision": 1e-6,
                "CutOff": 12.0,
            },
            "System": {
                "tcc1rs": {
                    "type": "Framework",
                    "UnitCells": "1 1 1",
                    "HeliumVoidFraction": 0.149,
                    "ExternalTemperature": 300.0,
                    "ExternalPressure": 5e5,
                },
            },
            "Component": {
                "methane": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                }
            },
        }
    )

    # framework
    framework = CifData(file=os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "files", "TCC1RS.cif"))

    # restart file
    parent_folder = load_node(base_calc_pk).outputs.remote_folder

    # Contructing builder
    builder = raspa_code.get_builder()
    builder.framework = {
        "tcc1rs": framework,
    }
    builder.parameters = parameters
    builder.parent_folder = parent_folder
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
        print("Testing RASPA with simple input, binary restart ...")
        res, pk = run_get_pk(builder)
        print("calculation pk: ", pk)
        print("Total Energy average (tcc1rs):", res["output_parameters"].dict.tcc1rs["general"]["total_energy_average"])
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
@click.option("--previous_calc", "-p", required=True, type=int, help="PK of example_base.py calculation")
@click.option("--submit", is_flag=True, help="Actually submit calculation")
def cli(codelabel, previous_calc, submit):
    """Click interface"""
    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print(f"The code '{codelabel}' does not exist")
        sys.exit(1)
    example_binary_restart(code, previous_calc, submit)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

# EOF
