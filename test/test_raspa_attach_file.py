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
    "NumberOfCycles"                   : 25000,
    "NumberOfInitializationCycles"     : 2000,
    "PrintEvery"                       : 1000,
    "Forcefield"                       : "zeolite",
    "Framework"                        : 0,
    "FrameworkName"                    : "ACO",
    "UnitCells"                        : "3 3 3",
    "HeliumVoidFraction"               : 0.29,
    "ExternalTemperature"              : 300.0,
    "ExternalPressure"                 : 1e5,
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
    })
calc.use_parameters(parameters)

# Additional files
pwd = os.path.dirname(os.path.realpath(__file__))
framework = SinglefileData(file=pwd+'/test_raspa_attach_file/ACO.cif')
calc.use_file(framework, linkname="framework")

molecule = SinglefileData (file=pwd+'/test_raspa_attach_file/methane.def')
calc.use_file(molecule, linkname="molecule")

molecule = SinglefileData (file=pwd+'/test_raspa_attach_file/force_field_mixing_rules.def')
calc.use_file(molecule, linkname="mixing_rules")


molecule = SinglefileData (file=pwd+'/test_raspa_attach_file/force_field.def')
calc.use_file(molecule, linkname="force_field")

molecule = SinglefileData (file=pwd+'/test_raspa_attach_file/pseudo_atoms.def')
calc.use_file(molecule, linkname="pseudo_atoms")

# resources
calc.set_max_wallclock_seconds(3*60)  # 3 min
calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine":1})

# store and submit
calc.store_all()
calc.submit()

#calc.submit_test()
print("submitted calculation: PK=%s" % calc.pk)

# EOF
