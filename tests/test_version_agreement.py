# -*- coding: utf-8 -*-
"""Check versions"""
from __future__ import print_function
from __future__ import absolute_import

import sys
import json
import aiida_raspa


def test_version_agreement():
    """Check if versions in setup.json and in plugin are consistent"""
    version1 = aiida_raspa.__version__
    with open("setup.json") as fhandle:
        version2 = json.load(fhandle)['version']

    if version1 != version2:
        print("ERROR: Versions in aiida_raspa/__init__.py and setup.json are inconsistent: {} vs {}".format(
            version1, version2))
        sys.exit(3)
