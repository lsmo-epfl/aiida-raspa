"""Run RASPA calculation with blocked pockets."""
import sys

import click
from aiida import orm
from aiida.common import NotExistent
from aiida.engine import run, run_get_pk
from importlib_resources import files

import aiida_raspa


def example_block_pockets(raspa_code, submit=True):
    """Prepare and submit RASPA calculation with blocked pockets."""

    # parameters
    parameters = orm.Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 500,
                "NumberOfInitializationCycles": 50,
                "PrintEvery": 10,
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
                }
            },
            "Component": {
                "methane": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                    "BlockPocketsFileName": "block_tcc1rs_methane",
                }
            },
        }
    )

    # framework
    framework = orm.CifData(file=(files(aiida_raspa).parent / "examples" / "files" / "TCC1RS.cif").as_posix())

    # block pocket
    block_pocket_node = orm.SinglefileData(
        file=(files(aiida_raspa).parent / "examples" / "files" / "block_pocket.block").as_posix()
    ).store()

    # Contructing builder
    builder = raspa_code.get_builder()
    builder.framework = {
        "tcc1rs": framework,
    }
    builder.block_pocket = {
        "block_tcc1rs_methane": block_pocket_node,
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
        print("Testing RASPA with block pockets ...")
        res, pk = run_get_pk(builder)
        print("calculation pk: ", pk)
        print(
            "Average number of methane molecules/uc:",
            res["output_parameters"].dict.tcc1rs["components"]["methane"]["loading_absolute_average"],
        )
        print("OK, calculation has completed successfully")
    else:
        print("Generating test input ...")
        builder.metadata.dry_run = True
        builder.metadata.store_provenance = False
        run(builder)
        print("Submission test successful")
        print("In order to actually submit, add '--submit'")


@click.command("cli")
@click.argument("codelabel")
@click.option("--submit", is_flag=True, help="Actually submit calculation")
def cli(codelabel, submit):
    """Click interface"""
    try:
        code = orm.load_code(codelabel)
    except NotExistent:
        print(f"The code '{codelabel}' does not exist")
        sys.exit(1)
    example_block_pockets(code, submit)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter

# EOF
