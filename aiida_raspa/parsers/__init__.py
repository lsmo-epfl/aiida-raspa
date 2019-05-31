# -*- coding: utf-8 -*-
"""Raspa output parser."""
from __future__ import absolute_import
import os
from six.moves import range

from aiida.common import NotExistent, OutputParsingError
from aiida.engine import ExitCode
from aiida.orm import Dict
from aiida.parsers.parser import Parser
from aiida_raspa.utils import parse_base_output

# parser
# --------------------------------------------------------------------------------------------


class RaspaParser(Parser):
    """Parse RASPA output"""

    # --------------------------------------------------------------------------
    def parse(self, **kwargs):
        """Receives in input a dictionary of retrieved nodes. Does all the logic here."""
        try:
            out_folder = self.retrieved
        except NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER

        for ftmp in out_folder._repository.list_object_names():  # pylint: disable=protected-access
            if ftmp.endswith('.data'):
                fname = ftmp
                break
        else:
            raise OutputParsingError("Calculation did not produce an output file. Please make sure that it run "
                                     "correctly")
        inp_params = self.node.inputs.parameters.get_dict()
        ncomponents = len(inp_params['Component'])
        component_names = []
        for i in range(ncomponents):
            component_names.append(inp_params['Component'][i]['MoleculeName'])

        # self.logger.info("list of components: {}".format(component_names))
        output_abs_path = os.path.join(out_folder._repository._get_base_folder().abspath, fname)  # pylint: disable=protected-access
        for key, value in parse_base_output(output_abs_path, ncomponents, component_names).items():
            self.out(key, Dict(dict=value))
        return ExitCode(0)
