# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c), The AiiDA team. All rights reserved.                        #
# This file is part of the AiiDA code.                                       #
#                                                                            #
# The code is hosted on GitHub at https://github.com/yakutovicha/aiida-raspa #
# For further information on the license, see the LICENSE.txt file           #
# For further information please visit http://www.aiida.net                  #
##############################################################################

__version__ = "0.2.1"

import re
from aiida.parsers.parser import Parser
from aiida.orm.data.parameter import ParameterData
from aiida_raspa.calculations import RaspaCalculation
from aiida.parsers.exceptions import OutputParsingError


def block_analysis(fl, value=1, units=2, dev=4):
    for line in fl:
        if 'Average' in line:
            break
    return (float(line.split()[value]), line.split()[units][1:-1],
            float(line.split()[dev]))


def extract_component_quantity(res_components, components, line, prop):
    # self.logger.info("analysing line: {}".format(line))
    for i, c in enumerate(components):
        if '['+c+']' in line:
            words = line.split()
            res_components[i][prop+'_units'] = words[-1][1:-1]
            res_components[i][prop+'_dev'] = float(words[-2])
            res_components[i][prop] = float(words[-4])
            return
    raise OutputParsingError("Could not find the property {} for any of the"
                             " components: {} in line {}. Last component"
                             " checked was: {}".format(prop, components,
                                                       line, c))


class RaspaParser(Parser):
    """
    Parser for the output of RASPA.
    """
#    _linkname_outparams = "component_0"

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
        fn = None
        fs = out_folder.get_folder_list()
        for f in fs:
            if f.endswith('.data'):
                fn = f
        if fn is None:
            raise OutputParsingError("Calculation did not produce an output"
                    " file. Please make sure that it run correctly")

        res_per_component = []
        component_names = []
        inp_params = self._calc.inp.parameters.get_dict()
        for i in range(len(inp_params['Component'])):
            res_per_component.append({})
            component_names.append(inp_params['Component'][i]['MoleculeName'])
        # self.logger.info("list of components: {}".format(component_names))

        result_dict = {'exceeded_walltime': False}
        abs_fn = out_folder.get_abs_path(fn)
        av_volume = re.compile("Average Volume:")
        av_pressure = re.compile("Average Pressure:")
        av_temperature = re.compile("Average temperature:")
        av_density = re.compile("Average Density:")
        av_heat_of_desorpt = re.compile("Heat of desorption:")
        av_tot_energy = re.compile("Total energy:$")
        num_of_molec = re.compile("Number of molecules:$")

        av_chem_pot_component = re.compile(" Average chemical potential: ")
        av_henry_coeff_component = re.compile(" Average Henry coefficient: ")

        result_dict = {'exceeded_walltime': False}
        with open(abs_fn, "r") as f:
            for line in f:
                if 'Finishing simulation' in line:
                    break
            for line in f:
                if av_volume.match(line) is not None:
                    (result_dict['cell_volume_average'],
                    result_dict['cell_volume_units'],
                    result_dict['cell_volume_dev']) = block_analysis(f)
                    continue

                if av_pressure.match(line) is not None:
                    (result_dict['pressure_average'],
                    result_dict['pressure_units'],
                    result_dict['pressure_dev']) = block_analysis(f)
                    continue

                if av_temperature.match(line) is not None:
                    (result_dict['temperature_average'],
                    result_dict['temperature_units'],
                    result_dict['temperature_dev']) = block_analysis(f)
                    continue

                if av_density.match(line) is not None:
                    (result_dict['density_average'],
                    result_dict['density_units'],
                    result_dict['density_dev']) = block_analysis(f)
                    continue

                if av_heat_of_desorpt.match(line) is not None:
                    (result_dict['heat_of_desorption_average'],
                    result_dict['heat_of_desorption_units'],
                    result_dict['heat_of_desorption_dev']) = \
                    block_analysis(f, units=4, dev=3)
                    continue

                if av_tot_energy.match(line) is not None:
                    (result_dict['total_energy_average'],
                    result_dict['total_energy_units'],
                    result_dict['total_energy_dev']) = \
                    block_analysis(f)
                    continue

                if num_of_molec.match(line) is not None:
                    break
#                if 'warnings' in line:
#                    result_dict['nwarnings'] = int(line.split()[-2])
            i = 0
            for line in f:
                if 'Average loading excess [molecules/unit cell]' in line:
                    res_per_component[i]['loading_absolute_average'] = \
                            float(line.split()[5])
                    res_per_component[i]['loading_absolute_dev'] = \
                            float(line.split()[7])
                    res_per_component[i]['loading_absolute_units'] = \
                            'molecules/unit cell'
                    i += 1
                    break
#                if 'exceeded requested execution time' in line:
#                    result_dict['exceeded_walltime'] = True
#            self.logger.error("before henry {}".format(res_per_component))
            for line in f:
                if av_henry_coeff_component.search(line):
                    extract_component_quantity(res_per_component,
                            component_names, line, "average_henry_coefficient")

                if av_chem_pot_component.search(line):
                    extract_component_quantity(res_per_component,
                            component_names, line,
                            "average_chemical_potential")

        pair = (self.get_linkname_outparams(), ParameterData(dict=result_dict))
        new_nodes_list.append(pair)
        for i, item in enumerate(res_per_component):
            pair = ('component_'+str(i), ParameterData(dict=item))
            new_nodes_list.append(pair)

# EOF
