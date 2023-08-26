"""Run RASPA calculation using Local force field"""
import os
import sys

import click
from aiida.common import NotExistent
from aiida.engine import run, run_get_pk
from aiida.orm import CifData, Code, Dict, SinglefileData


def example_ff_files(raspa_code, submit=True):
    """Prepare and submit RASPA calculation with components mixture."""

    # parameters
    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfInitializationCycles": 50,
                "NumberOfCycles": 50,
                "PrintEvery": 10,
                "Forcefield": "Local",
                "ChargeMethod": "Ewald",
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
                "CO2": {
                    "MoleculeDefinition": "Local",
                    "MolFraction": 0.30,
                    "TranslationProbability": 1.0,
                    "RotationProbability": 1.0,
                    "ReinsertionProbability": 1.0,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                },
                "N2": {
                    "MoleculeDefinition": "Local",
                    "MolFraction": 0.70,
                    "TranslationProbability": 1.0,
                    "RotationProbability": 1.0,
                    "ReinsertionProbability": 1.0,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                },
            },
        }
    )

    # Contructing builder
    pwd = os.path.dirname(os.path.realpath(__file__))
    builder = raspa_code.get_builder()
    builder.framework = {
        "irmof_1": CifData(file=os.path.join(pwd, "..", "files", "IRMOF-1_eqeq.cif")),
    }
    # Note: Here the SinglefileData in the dict are stored otherwise the dry_run crashes.
    #       However, this is not needed for real calculations (e.g., using --submit), since the work chains stores them.
    builder.file = {
        "file_1": SinglefileData(file=os.path.join(pwd, "..", "files", "force_field_mixing_rules.def")).store(),
        "file_2": SinglefileData(file=os.path.join(pwd, "..", "files", "pseudo_atoms.def")).store(),
        "file_3": SinglefileData(file=os.path.join(pwd, "..", "files", "CO2.def")).store(),
        "file_4": SinglefileData(file=os.path.join(pwd, "..", "files", "N2.def")).store(),
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
        print("Testing RASPA CO2/N2 adsorption in IRMOF-1, using Local force field ...")
        res, pk = run_get_pk(builder)
        print("calculation pk: ", pk)
        # pylint: disable=consider-using-f-string
        print(
            "CO2/N2 uptake ({:s}): {:.2f}/{:.2f} ".format(
                res["output_parameters"]["irmof_1"]["components"]["N2"]["loading_absolute_unit"],
                res["output_parameters"]["irmof_1"]["components"]["CO2"]["loading_absolute_average"],
                res["output_parameters"]["irmof_1"]["components"]["N2"]["loading_absolute_average"],
            )
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
    example_ff_files(code, submit)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

# EOF
