#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c), The AiiDA team. All rights reserved.                        #
# This file is part of the AiiDA code.                                       #
#                                                                            #
# The code is hosted on GitHub at https://github.com/yakutovicha/aiida-raspa #
# For further information on the license, see the LICENSE.txt file           #
# For further information please visit http://www.aiida.net                  #
##############################################################################
from __future__ import print_function

import sys

from aiida import load_dbenv, is_dbenv_loaded
from aiida.backends import settings
if not is_dbenv_loaded():
    load_dbenv(profile=settings.AIIDADB_PROFILE)

from aiida.common.example_helpers import test_and_get_code  
from aiida.orm.data.structure import StructureData  
from aiida.orm.data.parameter import ParameterData 
from aiida.orm.data.singlefile import SinglefileData


# ==============================================================================
if len(sys.argv) != 2:
    print("Usage: test_raspa.py <code_name>")
    sys.exit(1)

codename = sys.argv[1]
code = test_and_get_code(codename, expected_code_type='raspa')

print("Testing RASPA...")

# calc object
calc = code.new_calc()

# parameters
parameters = ParameterData(dict={
    "GeneralSettings":
    {
    "SimulationType"                   : "MonteCarlo",
    "NumberOfCycles"                   : 2000,
    "NumberOfInitializationCycles"     : 1000,
    "RestartFile"                      : False,
    "PrintEvery"                       : 1000,
    "Forcefield"                       : "GarciaPerez2006",
    "ModifyOxgensConnectedToAluminium" : True,
    "Framework"                        : 0,
    "FrameworkName"                    : "LTA4A",
    "RemoveAtomNumberCodeFromLabel"    : True,
    "UnitCells"                        : [1, 1, 1],
    "ExternalTemperature"              : 298.0,
    "ExternalPressure"                 : 10000.0,
    },
    "Component":
    [{
    "MoleculeName"                     : "sodium",
    "MoleculeDefinition"               : "TraPPE",
    "TranslationProbability"           :  1.0,
    "RandomTranslationProbability"     :  1.0,
    "ExtraFrameworkMolecule"           :  True,
    "CreateNumberOfMolecules"          :  96,
    },
    {
    "MoleculeName"                     : "CO2",
    "MoleculeDefinition"               : "TraPPE",
    "BlockPockets"                     : True,
    "BlockPocketsFilename"             : "LTA",
    "TranslationProbability"           : 1.0,
    "ReinsertionProbability"           : 1.0,
    "SwapProbability"                  : 1.0,
    "ExtraFrameworkMolecule"           : False,
    "CreateNumberOfMolecules"          : 0,
    }],
    })
calc.use_parameters(parameters)

# resources
calc.set_max_wallclock_seconds(30*60)  # 30 min
calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine":1})
#calc.set_queue_name("serial")
# store and submit
calc.store_all()
calc.submit()

#calc.submit_test()
print("submitted calculation: PK=%s" % calc.pk)

# EOF
