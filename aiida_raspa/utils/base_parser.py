# -*- coding: utf-8 -*-
"""Basic raspa output parser."""
from __future__ import absolute_import
from __future__ import print_function
import re

from math import isnan, isinf
from six.moves import range
from six.moves import zip

float_base = float  # pylint: disable=invalid-name


def float(number):  # pylint: disable=redefined-builtin
    number = float_base(number)
    return number if not any((isnan(number), isinf(number))) else None


KELVIN_TO_KJ_PER_MOL = float(8.314464919 / 1000.0)  #exactly the same as Raspa

# manage block of the first type
# --------------------------------------------------------------------------------------------
BLOCK_1_LIST = [
    (re.compile("Average Volume:"), "cell_volume", (1, 2, 4), 0),
    (re.compile("Average Pressure:"), "pressure", (1, 2, 4), 0),
    (re.compile("Average temperature:"), "temperature", (1, 2, 4), 0),
    (re.compile("Average Density:"), "adsorbate_density", (1, 2, 4), 0),
    (re.compile("Total energy:$"), "total_energy", (1, 2, 4), 0),
    (re.compile("Average Heat Capacity"), "framework_heat_capacity", (1, 2, 4), 0),
    (re.compile("Heat of desorption:"), "heat_of_desorption", (1, 4, 3), 4),
    (re.compile("Enthalpy of adsorption:"), "enthalpy_of_adsorption", (1, 4, 3), 4),
    (re.compile(".*Total enthalpy of adsorption from components and measured mol-fraction"),
     "enthalpy_of_adsorption_total_molfrac", (1, 4, 3), 0),
]

# block of box properties.
BOX_PROP_LIST = [
    (re.compile("Average Box-lengths:"), 'box'),
]


# pylint: disable=too-many-arguments
def parse_block1(flines, result_dict, prop, value=1, unit=2, dev=4):
    """Parse block that looks as follows:
    Average Volume:
    =================
        Block[ 0]        12025.61229 [A^3]
        Block[ 1]        12025.61229 [A^3]
        Block[ 2]        12025.61229 [A^3]
        Block[ 3]        12025.61229 [A^3]
        Block[ 4]        12025.61229 [A^3]
        ------------------------------------------------------------------------------
        Average          12025.61229 [A^3] +/-            0.00000 [A^3]
    """
    for line in flines:
        if 'Average' in line:
            result_dict[prop + '_average'] = float(line.split()[value])
            result_dict[prop + '_unit'] = re.sub(r"[{}()\[\]]", '', line.split()[unit])
            result_dict[prop + '_dev'] = float(line.split()[dev])
            break


# manage energy block
# --------------------------------------------------------------------------------------------
ENERGY_BLOCK_LIST = [
    (re.compile("Average Adsorbate-Adsorbate energy:"), 'ads_ads'),
    (re.compile("Average Host-Adsorbate energy:"), 'host_ads'),
]


def parse_block_energy(flines, res_dict, prop):
    """Parse block that looks as follows:
    Average Adsorbate-Adsorbate energy:
    ===================================
        Block[ 0] -443.23204         Van der Waals: -443.23204         Coulomb: 0.00000            [K]
        Block[ 1] -588.20205         Van der Waals: -588.20205         Coulomb: 0.00000            [K]
        Block[ 2] -538.43355         Van der Waals: -538.43355         Coulomb: 0.00000            [K]
        Block[ 3] -530.00960         Van der Waals: -530.00960         Coulomb: 0.00000            [K]
        Block[ 4] -484.15106         Van der Waals: -484.15106         Coulomb: 0.00000            [K]
        ------------------------------------------------------------------------------
        Average   -516.80566         Van der Waals: -516.805659        Coulomb: 0.00000            [K]
              +/- 98.86943                      +/- 98.869430               +/- 0.00000            [K]
    """
    for line in flines:
        if 'Average' in line:
            res_dict[prop + '_total_energy_unit'] = 'kJ/mol'
            res_dict[prop + '_vdw_energy_unit'] = 'kJ/mol'
            res_dict[prop + '_coulomb_energy_unit'] = 'kJ/mol'
            res_dict[prop + '_total_energy_average'] = float(line.split()[1]) * KELVIN_TO_KJ_PER_MOL
            res_dict[prop + '_vdw_energy_average'] = float(line.split()[5]) * KELVIN_TO_KJ_PER_MOL
            res_dict[prop + '_coulomb_energy_average'] = float(line.split()[7]) * KELVIN_TO_KJ_PER_MOL
        if '+/-' in line:
            res_dict[prop + '_total_energy_dev'] = float(line.split()[1]) * KELVIN_TO_KJ_PER_MOL
            res_dict[prop + '_vdw_energy_dev'] = float(line.split()[3]) * KELVIN_TO_KJ_PER_MOL
            res_dict[prop + '_coulomb_energy_dev'] = float(line.split()[5]) * KELVIN_TO_KJ_PER_MOL
            return


# manage lines with components
# --------------------------------------------------------------------------------------------
LINES_WITH_COMPONENT_LIST = [
    (re.compile(" Average chemical potential: "), "chemical_potential"),
    (re.compile(" Average Henry coefficient: "), "henry_coefficient"),
    (re.compile(" Average  <U_gh>_1-<U_h>_0:"), "adsorption_energy_widom"),
    (re.compile(" Average Widom Rosenbluth-weight:"), "widom_rosenbluth_factor"),
]


def parse_lines_with_component(res_components, components, line, prop):
    """Parse lines that contain components"""
    # self.logger.info("analysing line: {}".format(line))
    for i, component in enumerate(components):
        if '[' + component + ']' in line:
            words = line.split()
            res_components[i][prop + '_unit'] = re.sub(r'[{}()\[\]]', '', words[-1])
            res_components[i][prop + '_dev'] = float(words[-2])
            res_components[i][prop + '_average'] = float(words[-4])


# pylint: disable=too-many-locals, too-many-arguments, too-many-statements, too-many-branches
def parse_base_output(output_abs_path, system_name, ncomponents):
    """Parse RASPA output file"""

    warnings = []
    res_per_component = []
    for i in range(ncomponents):
        res_per_component.append({})
    result_dict = {'exceeded_walltime': False}
    framework_density = re.compile("Framework Density:")
    num_of_molec = re.compile("Number of molecules:$")

    with open(output_abs_path, "r") as fobj:
        # 1st parsing part
        icomponent = 0
        component_names = []
        res_cmp = res_per_component[0]
        for line in fobj:
            if "Component" in line and "(Adsorbate molecule)" in line:
                component_names.append(line.split()[2][1:-1])
            # Consider to change it with parse_line()
            if "Conversion factor molecules/unit cell -> mol/kg:" in line:
                res_cmp['conversion_factor_molec_uc_to_mol_kg'] = float(line.split()[6])
                res_cmp['conversion_factor_molec_uc_to_mol_kg_unit'] = "(mol/kg)/(molec/uc)"
            if "Conversion factor molecules/unit cell -> gr/gr:" in line:
                res_cmp['conversion_factor_molec_uc_to_gr_gr'] = float(line.split()[6])
                res_cmp['conversion_factor_molec_uc_to_gr_gr_unit'] = "(gr/gr)/(molec/uc)"
            if "Conversion factor molecules/unit cell -> cm^3 STP/gr:" in line:
                res_cmp['conversion_factor_molec_uc_to_cm3stp_gr'] = float(line.split()[7])
                res_cmp['conversion_factor_molec_uc_to_cm3stp_gr_unit'] = "(cm^3_STP/gr)/(molec/uc)"
            if "Conversion factor molecules/unit cell -> cm^3 STP/cm^3:" in line:
                res_cmp['conversion_factor_molec_uc_to_cm3stp_cm3'] = float(line.split()[7])
                res_cmp['conversion_factor_molec_uc_to_cm3stp_cm3_unit'] = "(cm^3_STP/cm^3)/(molec/uc)"
            if "MolFraction:" in line:
                res_cmp['mol_fraction'] = float(line.split()[1])
                res_cmp['mol_fraction_unit'] = "-"
            if "Partial pressure:" in line:
                res_cmp['partial_pressure'] = float(line.split()[2])
                res_cmp['partial_pressure_unit'] = "Pa"
            if "Partial fugacity:" in line:
                res_cmp['partial_fugacity'] = float(line.split()[2])
                res_cmp['partial_fugacity_unit'] = "Pa"
                icomponent += 1
                if icomponent < ncomponents:
                    res_cmp = res_per_component[icomponent]
                else:
                    break
        # end of the 1st parsing part

        # 2nd parsing part
        for line in fobj:
            for parse in BLOCK_1_LIST:
                if parse[0].match(line):
                    parse_block1(fobj, result_dict, parse[1], *parse[2])
                    # I assume here that properties per component are present furhter in the output file.
                    # so I need to skip some lines:
                    skip_nlines_after = parse[3]
                    while skip_nlines_after > 0:
                        line = next(fobj)
                        skip_nlines_after -= 1
                    for i, cmpnt in enumerate(component_names):
                        # The order of properties per molecule is the same as the order of molecules in the
                        # input file. So if component name was not found in the next line, I break the loop
                        # immidiately as there is no reason to continue it
                        line = next(fobj)
                        if cmpnt in line:
                            parse_block1(fobj, res_per_component[i], parse[1], *parse[2])
                        else:
                            break
                        skip_nlines_after = parse[3]
                        while skip_nlines_after > 0:
                            line = next(fobj)
                            skip_nlines_after -= 1

                    continue  # no need to perform further checks, propperty has been found already
            for parse in ENERGY_BLOCK_LIST:
                if parse[0].match(line):
                    parse_block_energy(fobj, result_dict, prop=parse[1])
                    continue  # no need to perform further checks, propperty has been found already
            for parse in BOX_PROP_LIST:
                if parse[0].match(line):
                    # parse three cell vectors
                    parse_block1(fobj, result_dict, prop='box_ax', value=2, unit=3, dev=5)
                    parse_block1(fobj, result_dict, prop='box_by', value=2, unit=3, dev=5)
                    parse_block1(fobj, result_dict, prop='box_cz', value=2, unit=3, dev=5)
                    # parsee angles between the cell vectors
                    parse_block1(fobj, result_dict, prop='box_alpha', value=3, unit=4, dev=6)
                    parse_block1(fobj, result_dict, prop='box_beta', value=3, unit=4, dev=6)
                    parse_block1(fobj, result_dict, prop='box_gamma', value=3, unit=4, dev=6)
            if framework_density.match(line) is not None:
                result_dict['framework_density'] = line.split()[2]
                result_dict['framework_density_unit'] = re.sub(r'[{}()\[\]]', '', line.split()[3])

            elif num_of_molec.match(line) is not None:
                break  # this stops the cycle
        # end of the 2nd parsing part

        # 3rd parsing part
        icomponent = 0
        for line in fobj:
            # Consider to change it with parse_line?
            if 'Average loading absolute [molecules/unit cell]' in line:
                res_per_component[icomponent]['loading_absolute_average'] = float(line.split()[5])
                res_per_component[icomponent]['loading_absolute_dev'] = float(line.split()[7])
                res_per_component[icomponent]['loading_absolute_unit'] = 'molecules/unit cell'
            elif 'Average loading excess [molecules/unit cell]' in line:
                res_per_component[icomponent]['loading_excess_average'] = float(line.split()[5])
                res_per_component[icomponent]['loading_excess_dev'] = float(line.split()[7])
                res_per_component[icomponent]['loading_excess_unit'] = 'molecules/unit cell'
                icomponent += 1
            if icomponent >= ncomponents:
                break
        # end of the 3rd parsing part

        # 4th parsing part
        for line in fobj:
            for to_parse in LINES_WITH_COMPONENT_LIST:
                if to_parse[0].search(line):
                    parse_lines_with_component(res_per_component, component_names, line, to_parse[1])
        # end of the 4th parsing part

    return_dictionary = {"general": result_dict, "components": {}}

    for name, value in zip(component_names, res_per_component):
        return_dictionary["components"][name] = value

    with open(output_abs_path, "r") as fobj:
        for line in fobj:
            if "WARNING" in line:
                warnings.append((system_name, line))
    return return_dictionary, warnings
