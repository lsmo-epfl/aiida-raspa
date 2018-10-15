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

KELVIN_TO_KJ_PER_MOL=float(8.314464919/1000.0) #exactly the same as Raspa


'''
def block_analysis(fl, value=1, units=2, dev=4):                    #domod: not useful
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
'''


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
        ncomponents = len(inp_params['Component'])
        for i in range(ncomponents):
            res_per_component.append({})
            component_names.append(inp_params['Component'][i]['MoleculeName'])
        # self.logger.info("list of components: {}".format(component_names))

        abs_fn = out_folder.get_abs_path(fn)

        with open(abs_fn, "r") as f:
            # Parse the "Adsorbate properties" section
            if ncomponents>0:
                icomponent = 0
                for line in f:
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

            # Jump to the "Results" section (if not present: exceeded_walltime=True)   
            result_dict = {'exceeded_walltime': True}
            for line in f: 
                if 'Finishing simulation' in line:
                    result_dict['exceeded_walltime'] = False 
                    break    

            # Parse the "System results" section                        
            for line in f:
                if 'Enthalpy of adsorption:' in line: 
                    for line in f: 
                        if 'Average' in line:
                            result_dict['enthalpy_of_adsorption_units']   = 'KJ/MOL'
                            result_dict['enthalpy_of_adsorption_average'] = float(line.split()[1])*KELVIN_TO_KJ_PER_MOL
                            result_dict['enthalpy_of_adsorption_dev']     = float(line.split()[3])*KELVIN_TO_KJ_PER_MOL
                            break
                break
            for line in f: 
                if 'Average Adsorbate-Adsorbate energy:' in line:
                    for line in f: 
                        if 'Average' in line:
                            result_dict['ads_ads_total_energy_unit']   = 'KJ/MOL'
                            result_dict['ads_ads_wdv_energy_unit']     = 'KJ/MOL'
                            result_dict['ads_ads_coulomb_energy_unit'] = 'KJ/MOL'
                            result_dict['ads_ads_total_energy_average']   = float(line.split()[1])*KELVIN_TO_KJ_PER_MOL
                            result_dict['ads_ads_wdv_energy_average']     = float(line.split()[5])*KELVIN_TO_KJ_PER_MOL
                            result_dict['ads_ads_coulomb_energy_average'] = float(line.split()[7])*KELVIN_TO_KJ_PER_MOL
                        if '+/-' in line:
                            result_dict['ads_ads_total_energy_dev']   = float(line.split()[1])*KELVIN_TO_KJ_PER_MOL
                            result_dict['ads_ads_wdv_energy_dev']     = float(line.split()[3])*KELVIN_TO_KJ_PER_MOL
                            result_dict['ads_ads_coulomb_energy_dev'] = float(line.split()[5])*KELVIN_TO_KJ_PER_MOL    
                            break
                    break 
            for line in f: 
                if 'Average Host-Adsorbate energy:' in line:
                    for line in f: 
                        if 'Average' in line:
                            result_dict['host_ads_total_energy_unit']   = 'KJ/MOL'
                            result_dict['host_ads_wdv_energy_unit']     = 'KJ/MOL'
                            result_dict['host_ads_coulomb_energy_unit'] = 'KJ/MOL'
                            result_dict['host_ads_total_energy_average']   = float(line.split()[1])*KELVIN_TO_KJ_PER_MOL
                            result_dict['host_ads_wdv_energy_average']     = float(line.split()[5])*KELVIN_TO_KJ_PER_MOL
                            result_dict['host_ads_coulomb_energy_average'] = float(line.split()[7])*KELVIN_TO_KJ_PER_MOL
                        if '+/-' in line:
                            result_dict['host_ads_total_energy_dev']   = float(line.split()[1])*KELVIN_TO_KJ_PER_MOL
                            result_dict['host_ads_wdv_energy_dev']     = float(line.split()[3])*KELVIN_TO_KJ_PER_MOL
                            result_dict['host_ads_coulomb_energy_dev'] = float(line.split()[5])*KELVIN_TO_KJ_PER_MOL    
                            break
                    break

            # Jump to the "Adsorbate results" section   
            for line in f: 
                if 'Number of molecules:' in line:
                    break

            # Parse the "Adsorbate results" section
            if ncomponents>0:
                icomponent = 0  
                for line in f:
                    if 'Average loading absolute [molecules/unit cell]' in line:
                        res_per_component[icomponent]['loading_absolute_average'] = float(line.split()[5])
                        res_per_component[icomponent]['loading_absolute_dev'] = float(line.split()[7])
                        res_per_component[icomponent]['loading_absolute_units'] = 'molec/uc'
                    if 'Average loading excess [molecules/unit cell]' in line:
                        res_per_component[icomponent]['loading_excess_average'] = float(line.split()[5])
                        res_per_component[icomponent]['loading_excess_dev'] = float(line.split()[7])
                        res_per_component[icomponent]['loading_excess_units'] = 'molec/uc'
                        icomponent += 1
                    if icomponent == ncomponents:
                        break

            for line in f: 
                if 'Average Henry coefficient:' in line:
                   for line in f:
                       for icomponent in range(len(component_names)):
                           if component_names[icomponent] in line: 
                               res_per_component[icomponent]['average_henry_coefficient_units'] = 'mol/kg/Pa'
                               res_per_component[icomponent]['average_henry_coefficient'] = float(line.split()[4])
                               res_per_component[icomponent]['average_henry_coefficient_dev'] = float(line.split()[6])
                       if 'Average adsorption energy' in line:
                           break
                   break 
            #End of the Raspa file   

        pair = (self.get_linkname_outparams(), ParameterData(dict=result_dict))
        new_nodes_list.append(pair)
        for i, item in enumerate(res_per_component):
            pair = ('component_'+str(i), ParameterData(dict=item))
            new_nodes_list.append(pair)

# EOF
