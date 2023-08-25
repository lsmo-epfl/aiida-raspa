"""Run RASPA calculation to compute Henry coefficient."""
import os
import sys

import click
from aiida.common import NotExistent
from aiida.engine import run, run_get_pk
from aiida.orm import Code, Dict
from aiida.plugins import DataFactory

# data objects
CifData = DataFactory("cif")  # pylint: disable=invalid-name


def example_henry(raspa_code, submit=True):
    """Prepare and submit simple RASPA calculation to compute Henry coefficient."""

    # parameters
    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 50,
                "PrintPropertiesEvery": 10,
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
                }
            },
            "Component": {
                "methane": {
                    "MoleculeDefinition": "TraPPE",
                    "WidomProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                }
            },
        }
    )

    # framework
    pwd = os.path.dirname(os.path.realpath(__file__))
    framework = CifData(file=os.path.join(pwd, "..", "files", "TCC1RS.cif"))

    # Contructing builder
    builder = raspa_code.get_builder()
    builder.framework = {
        "tcc1rs": framework,
    }
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
        print("Testing RASPA on computing Henry coefficient ...")
        res, pk = run_get_pk(builder)
        print("calculation pk: ", pk)
        print(
            "Average Henry coefficient (methane in tcc1rs):",
            res["output_parameters"].dict.tcc1rs["components"]["methane"]["henry_coefficient_average"],
        )
        print("OK, calculation has completed successfully")
    else:
        print("Generating test input ...")
        builder.metadata.dry_run = True
        builder.metadata.store_provenance = False
        run(builder)
        print("submission test successful")
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
    example_henry(code, submit)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

# EOF
