"""Raspa output parser."""
import os
from pathlib import Path

from aiida.common import NotExistent, OutputParsingError
from aiida.engine import ExitCode
from aiida.orm import Dict, List
from aiida.parsers.parser import Parser

from aiida_raspa.utils import parse_base_output

# parser
# --------------------------------------------------------------------------------------------


class RaspaParser(Parser):
    """Parse RASPA output"""

    # --------------------------------------------------------------------------
    def parse(self, **kwargs):  # pylint: disable=too-many-locals
        """Receives in input a dictionary of retrieved nodes. Does all the logic here."""
        try:
            out_folder = self.retrieved
        except NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER
        output_folder_name = self.node.process_class.OUTPUT_FOLDER

        if output_folder_name not in out_folder.base.repository.list_object_names():  # pylint: disable=protected-access
            return self.exit_codes.ERROR_NO_OUTPUT_FILE

        output_parameters = {}
        warnings = []
        ncomponents = len(self.node.inputs.parameters.get_dict()["Component"])
        for system_id, system_name in enumerate(self.node.get_extra("system_order")):
            # specify the name for the system
            output_dir = Path(output_folder_name) / f"System_{system_id}"
            output_filename = out_folder.base.repository.list_object_names(output_dir).pop()
            output_contents = out_folder.base.repository.get_object_content(output_dir / output_filename)

            # Check for possible errors
            if "Starting simulation" not in output_contents:
                return self.exit_codes.ERROR_SIMULATION_DID_NOT_START
            if "Simulation finished" not in output_contents:
                return self.exit_codes.TIMEOUT

            # parse output parameters and warnings
            parsed_parameters, parsed_warnings = parse_base_output(output_contents, system_name, ncomponents)
            output_parameters[system_name] = parsed_parameters
            warnings += parsed_warnings

        self.out("output_parameters", Dict(dict=output_parameters))
        self.out("warnings", List(list=warnings))

        return ExitCode(0)
