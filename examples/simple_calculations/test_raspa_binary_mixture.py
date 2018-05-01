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
import os

from aiida import load_dbenv, is_dbenv_loaded
from aiida.backends import settings
if not is_dbenv_loaded():
    load_dbenv(profile=settings.AIIDADB_PROFILE)

from aiida.common.example_helpers import test_and_get_code  
from aiida.orm.data.cif import CifData 
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
    "NumberOfInitializationCycles"     : 2000,
    "PrintEvery"                       : 1000,
    "Forcefield"                       : "GarciaPerez2006",

    "Box"                              : 0,
    "BoxLengths"                       : "25 25 25",
    "ExternalTemperature"              : 300.0,
    },
    "Component":
    [{
    "MoleculeName"                     : "propane",
    "MoleculeDefinition"               : "TraPPE",
    "TranslationProbability"           : 1.0,
    "ReinsertionProbability"           : 1.0,
    "SwapProbability"                  : 1.0,
    "CreateNumberOfMolecules"          : 30,
    },
    {
    "MoleculeName"                     : "butane",
    "MoleculeDefinition"               : "TraPPE",
    "TranslationProbability"           : 1.0,
    "ReinsertionProbability"           : 1.0,
    "SwapProbability"                  : 1.0,
    "CreateNumberOfMolecules"          : 30,
    },
    ],  
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
