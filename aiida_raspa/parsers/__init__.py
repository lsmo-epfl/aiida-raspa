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

        ncomponents = len(self.node.inputs.parameters.get_dict()['Component'])

        # self.logger.info("list of components: {}".format(component_names))
        output_abs_path = os.path.join(out_folder._repository._get_base_folder().abspath, fname)  # pylint: disable=protected-access
        parsed_parameters = parse_base_output(output_abs_path, ncomponents)
        self.out("output_parameters", Dict(dict=parsed_parameters.pop("output_parameters")))
        for key, value in parsed_parameters.items():
            self.out("component.{}".format(key), Dict(dict=value))
        return ExitCode(0)
