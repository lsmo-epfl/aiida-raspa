# -*- coding: utf-8 -*-

from aiida.parsers.parser import Parser
from aiida.orm.data.parameter import ParameterData
from aiida_raspa.calculations import RaspaCalculation



class RaspaParser(Parser):
    """
    Parser for the output of RASPA.
    """

    # --------------------------------------------------------------------------
    def __init__(self, calc):
        """
        Initialize the instance of RaspaParser
        """
        super(RaspaParser, self).__init__(calc)

        # check for valid input
        if not isinstance(calc, RaspaCalculation):
            raise OutputParsingError("Input calc must be a RaspaCalculation")

    # --------------------------------------------------------------------------
    def parse_with_retrieved(self, retrieved):
        """
        Receives in input a dictionary of retrieved nodes.
        Does all the logic here.
        """
        out_folder = retrieved['retrieved']

        new_nodes_list = []
        self._parse_stdout(out_folder, new_nodes_list)
        return True, new_nodes_list

    def _parse_stdout(self, out_folder, new_nodes_list):
        #fn = self._calc._OUTPUT_FILE_NAME
        fs = out_folder.get_folder_list()
        for f in fs:
            if f.endswith('.data'):
                fn=f

        result_dict = {'exceeded_walltime': False}
        abs_fn = out_folder.get_abs_path(fn)
        with open(abs_fn, "r") as f:
            for line in f.readlines():
                if line.startswith('Number of Adsorbates:'):
                    result_dict['number_of_adsorbates'] = float(line.split()[3])
#                    result_dict['energy_units'] = "a.u."
#                if 'The number of warnings for this run is' in line:
#                    result_dict['nwarnings'] = int(line.split()[-1])
#                if 'exceeded requested execution time' in line:
#                    result_dict['exceeded_walltime'] = True

        pair = ('output_parameters', ParameterData(dict=result_dict))
        new_nodes_list.append(pair)
