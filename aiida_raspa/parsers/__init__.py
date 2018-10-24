# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c), The AiiDA team. All rights reserved.                        #
# This file is part of the AiiDA code.                                       #
#                                                                            #
# The code is hosted on GitHub at https://github.com/yakutovicha/aiida-raspa #
# For further information on the license, see the LICENSE.txt file           #
# For further information please visit http://www.aiida.net                  #
##############################################################################

__version__ = "0.2.2"

import re
from aiida.parsers.parser import Parser
from aiida.orm.data.parameter import ParameterData
from aiida_raspa.calculations import RaspaCalculation
from aiida.parsers.exceptions import OutputParsingError

KELVIN_TO_KJ_PER_MOL = float(8.314464919/1000.0) #exactly the same as Raspa

def block_analysis(fl, value=1, units=2, dev=4):
    for line in fl:
        if 'Average' in line:
            break
    return (float(line.split()[value]), line.split()[units].translate(None, '[](){}'), float(line.split()[dev]))


def parse_line(res_components, components, line, prop):
    # self.logger.info("analysing line: {}".format(line))
    for i, c in enumerate(components):
        if '['+c+']' in line:
            words = line.split()
            res_components[i][prop+'_units'] = words[-1].translate(None, '[](){}')
            res_components[i][prop+'_dev'] = float(words[-2])
            res_components[i][prop+'_average'] = float(words[-4])


class RaspaParser(Parser):
    """Parser for the output of RASPA."""

    # --------------------------------------------------------------------------
    def __init__(self, calc):
        """Initialize the instance of RaspaParser."""
        super(RaspaParser, self).__init__(calc)

        # check for valid input
        if not isinstance(calc, RaspaCalculation):
            raise OutputParsingError("Input calc must be a RaspaCalculation")

    # --------------------------------------------------------------------------
    def parse_with_retrieved(self, retrieved):
        """Receives in input a dictionary of retrieved nodes. Does all the logic here."""
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
            raise OutputParsingError("Calculation did not produce an output file. Please make sure that it run "
                    "correctly")

        res_per_component = []
        component_names = []
        inp_params = self._calc.inp.parameters.get_dict()
        ncomponents = len(inp_params['Component'])
        for i in range(ncomponents):
            res_per_component.append({})
            component_names.append(inp_params['Component'][i]['MoleculeName'])
        # self.logger.info("list of components: {}".format(component_names))

        output_abs_path = out_folder.get_abs_path(fn)
        result_dict = {'exceeded_walltime': False}
        
        results_list = [
                (re.compile("Average Volume:"), "cell_volume"),
                (re.compile("Average Pressure:"), "pressure"),
                (re.compile("Average temperature:"), "temperature"),
                (re.compile("Average Density:"), "density"),
                (re.compile("Total energy:$"), "total_energy"),
                (re.compile("Average Heat Capacity"), "framework_heat_capacity"),
                ]
        framework_density = re.compile("Framework Density:")
        av_heat_of_desorpt = re.compile("Heat of desorption:")
        num_of_molec = re.compile("Number of molecules:$")
        
        results_per_component_list = [
                (re.compile(" Average chemical potential: "), "chemical_potential"),
                (re.compile(" Average Henry coefficient: "), "henry_coefficient"),
                (re.compile(" Average  <U_gh>_1-<U_h>_0:"), "adsorption_energy_widom"),
                ]

        with open(output_abs_path, "r") as f:
            icomponent = 0
            for line in f:
                # TODO change for parse_line?
                if "MolFraction:" in line:
                    res_per_component[icomponent]['mol_fraction'] = float(line.split()[1])
                    res_per_component[icomponent]['mol_fraction_unit'] = "-"
                if "Conversion factor molecules/unit cell -> mol/kg:" in line:
                    res_per_component[icomponent]['conversion_factor_molec_uc_to_mol_kg'] = float(line.split()[6])
                    res_per_component[icomponent]['conversion_factor_molec_uc_to_mol_kg_unit'] = "(mol/kg)/(molec/uc)"
                if "Conversion factor molecules/unit cell -> gr/gr:" in line:
                    res_per_component[icomponent]['conversion_factor_molec_uc_to_gr_gr'] = float(line.split()[6])
                    res_per_component[icomponent]['conversion_factor_molec_uc_to_gr_gr_unit'] = "(gr/gr)/(molec/uc)"
                if "Conversion factor molecules/unit cell -> cm^3 STP/gr:" in line:
                    res_per_component[icomponent]['conversion_factor_molec_uc_to_cm3stp_gr'] = float(line.split()[7])
                    res_per_component[icomponent]['conversion_factor_molec_uc_to_cm3stp_gr_unit'] = "(cm^3_STP/gr)/(molec/uc)"
                if "Conversion factor molecules/unit cell -> cm^3 STP/cm^3:" in line:
                    res_per_component[icomponent]['conversion_factor_molec_uc_to_cm3stp_cm3'] = float(line.split()[7])
                    res_per_component[icomponent]['conversion_factor_molec_uc_to_cm3stp_cm3_unit'] = "(cm^3_STP/cm^3)/(molec/uc)"
                if "Partial pressure:" in line:
                    res_per_component[icomponent]['partial_pressure'] = float(line.split()[2])
                    res_per_component[icomponent]['partial_pressure_unit'] = "Pa"
                if "Partial fugacity:" in line:
                    res_per_component[icomponent]['partial_fugacity'] = float(line.split()[2])
                    res_per_component[icomponent]['partial_fugacity_unit'] = "Pa"
                    icomponent += 1
                if icomponent == ncomponents:
                    break
        
            for line in f:
                for parse in results_list:
                    if parse[0].match(line):
                        (result_dict[parse[1]+'_average'],
                         result_dict[parse[1]+'_units'],
                         result_dict[parse[1]+'_dev'],
                            ) = block_analysis(f)
                    continue
                
                if framework_density.match(line) is not None:
                    (result_dict['framework_density'], result_dict['framework_density_units']
                            ) = line.split()[2], line.split()[3].translate(None, '[](){}')
                    continue
        
                if av_heat_of_desorpt.match(line) is not None:
                    (result_dict['heat_of_desorption_average'], result_dict['heat_of_desorption_units'],
                    result_dict['heat_of_desorption_dev']) = block_analysis(f, units=4, dev=3)
                    continue
        
        
                if 'Average Adsorbate-Adsorbate energy:' in line:
                    for line in f:
                        if 'Average' in line:
                            result_dict['ads_ads_total_energy_unit']   = 'kJ/mol'
                            result_dict['ads_ads_vdw_energy_unit']     = 'kJ/mol'
                            result_dict['ads_ads_coulomb_energy_unit'] = 'kJ/mol'
                            result_dict['ads_ads_total_energy_average']   = float(line.split()[1])*KELVIN_TO_KJ_PER_MOL
                            result_dict['ads_ads_wdv_energy_average']     = float(line.split()[5])*KELVIN_TO_KJ_PER_MOL
                            result_dict['ads_ads_coulomb_energy_average'] = float(line.split()[7])*KELVIN_TO_KJ_PER_MOL
                        if '+/-' in line:
                            result_dict['ads_ads_total_energy_dev']   = float(line.split()[1])*KELVIN_TO_KJ_PER_MOL
                            result_dict['ads_ads_vdw_energy_dev']     = float(line.split()[3])*KELVIN_TO_KJ_PER_MOL
                            result_dict['ads_ads_coulomb_energy_dev'] = float(line.split()[5])*KELVIN_TO_KJ_PER_MOL
                            break
        
                if 'Average Host-Adsorbate energy:' in line:
                    for line in f:
                        if 'Average' in line:
                            result_dict['host_ads_total_energy_unit']   = 'kJ/mol'
                            result_dict['host_ads_vdw_energy_unit']     = 'kJ/mol'
                            result_dict['host_ads_coulomb_energy_unit'] = 'kJ/mol'
                            result_dict['host_ads_total_energy_average']   = float(line.split()[1])*KELVIN_TO_KJ_PER_MOL
                            result_dict['host_ads_wdv_energy_average']     = float(line.split()[5])*KELVIN_TO_KJ_PER_MOL
                            result_dict['host_ads_coulomb_energy_average'] = float(line.split()[7])*KELVIN_TO_KJ_PER_MOL
                        if '+/-' in line:
                            result_dict['host_ads_total_energy_dev']   = float(line.split()[1])*KELVIN_TO_KJ_PER_MOL
                            result_dict['host_ads_wdv_energy_dev']     = float(line.split()[3])*KELVIN_TO_KJ_PER_MOL
                            result_dict['host_ads_coulomb_energy_dev'] = float(line.split()[5])*KELVIN_TO_KJ_PER_MOL
                            break
        
                if num_of_molec.match(line) is not None:
                    break
        
            icomponent = 0
            for line in f:
        
                # TODO: change for parse_line?
                if 'Average loading absolute [molecules/unit cell]' in line:
                    res_per_component[icomponent]['loading_absolute_average'] = float(line.split()[5])
                    res_per_component[icomponent]['loading_absolute_dev'] = float(line.split()[7])
                    res_per_component[icomponent]['loading_absolute_units'] = 'molecules/unit cell'
                if 'Average loading excess [molecules/unit cell]' in line:
                    res_per_component[icomponent]['loading_excess_average'] = float(line.split()[5])
                    res_per_component[icomponent]['loading_excess_dev'] = float(line.split()[7])
                    res_per_component[icomponent]['loading_excess_units'] = 'molecules/unit cell'
                    icomponent += 1
                if icomponent >= ncomponents:
                    break
            for line in f:
                for to_parse in results_per_component_list:
                    if to_parse[0].search(line):
                        parse_line(res_per_component, component_names, line, to_parse[1])
        
        pair = (self.get_linkname_outparams(), ParameterData(dict=result_dict))
        new_nodes_list.append(pair)
        for i, item in enumerate(res_per_component):
            pair = ('component_'+str(i), ParameterData(dict=item))
            new_nodes_list.append(pair)

# EOF
