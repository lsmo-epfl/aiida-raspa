import os

from aiida.common.example_helpers import test_and_get_code  # noqa
from aiida.orm.data.cif import CifData 
from aiida.orm.data.parameter import ParameterData 
from aiida.work.run import submit

from aiida_raspa.workflows import RaspaConvergeWorkChain

options_dict = {
    "resources": {
        "num_machines": 1,
        "num_mpiprocs_per_machine": 1,
        },
    "max_wallclock_seconds": 3 * 60 * 60,
    }

options = ParameterData(dict=options_dict)

params_dict = {
    "GeneralSettings":
    {
    "SimulationType"                   : "MonteCarlo",
    "NumberOfCycles"                   : 2000,
    "NumberOfInitializationCycles"     : 2000,
    "PrintEvery"                       : 1000,
    "Forcefield"                       : "GenericMOFs",
    "EwaldPrecision"                   : 1e-6,
    "CutOff"                           : 12.0,
    "Framework"                        : 0,
    "UnitCells"                        : "1 1 1",
    "HeliumVoidFraction"               : 0.149,
    "ExternalTemperature"              : 300.0,
    "ExternalPressure"                 : 5e5,
    },
    "Component":
    [{
    "MoleculeName"                     : "methane",
    "MoleculeDefinition"               : "TraPPE",
    "TranslationProbability"           : 0.5,
    "ReinsertionProbability"           : 0.5,
    "SwapProbability"                  : 1.0,
    "CreateNumberOfMolecules"          : 0,
    }],
}
parameters = ParameterData(dict=params_dict)

# Additional files
pwd = os.path.dirname(os.path.realpath(__file__))
structure = CifData(file=pwd+'/test_raspa_attach_file/TCC1RS.cif')

code = test_and_get_code('raspa@deneb', expected_code_type='raspa')
submit(RaspaConvergeWorkChain,
        code=code,
        structure=structure,
        parameters=parameters,
        options=options,
        _label='MyFirstWokchain',
        ) 
