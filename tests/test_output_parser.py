"""Test Raspa output parser"""

from __future__ import absolute_import

import os

from aiida_raspa.utils import parse_base_output

CWD = os.path.dirname(os.path.realpath(__file__))


def test_parse_output_one_cmpnt():
    """Testing output parser on an output file with one component"""
    parsed_parameters = parse_base_output(os.path.join(CWD, "outputs/one_component.out"),
                                          system_name="system1",
                                          ncomponents=1)[0]
    general = {
        'exceeded_walltime': False,
        'framework_density': '739.995779685958',
        'framework_density_unit': 'kg/m^3',
        'temperature_average': 0.0,
        'temperature_unit': 'K',
        'temperature_dev': 0.0,
        'pressure_average': 0.0,
        'pressure_unit': 'Pa',
        'pressure_dev': 0.0,
        'cell_volume_average': 12025.61229,
        'cell_volume_unit': 'A^3',
        'cell_volume_dev': 0.0,
        'box_ax_average': 34.1995,
        'box_ax_unit': 'A^3',
        'box_ax_dev': 0.0,
        'box_by_average': 22.6557,
        'box_by_unit': 'A^3',
        'box_by_dev': 0.0,
        'box_cz_average': 15.52065,
        'box_cz_unit': 'A^3',
        'box_cz_dev': 0.0,
        'box_alpha_average': 90.0,
        'box_alpha_unit': 'degrees',
        'box_alpha_dev': 0.0,
        'box_beta_average': 52.8626,
        'box_beta_unit': 'degrees',
        'box_beta_dev': 0.0,
        'box_gamma_average': 90.0,
        'box_gamma_unit': 'degrees',
        'box_gamma_dev': 0.0,
        'adsorbate_density_average': 26.62672,
        'adsorbate_density_unit': 'kg/m^3',
        'adsorbate_density_dev': 5.35266,
        'framework_heat_capacity_average': 1689.95117,
        'framework_heat_capacity_unit': 'J/mol/K',
        'framework_heat_capacity_dev': 1594.19741,
        'enthalpy_of_adsorption_average': -1928.58214,
        'enthalpy_of_adsorption_unit': 'K',
        'enthalpy_of_adsorption_dev': 204.730157,
        'ads_ads_total_energy_unit': 'kJ/mol',
        'ads_ads_vdw_energy_unit': 'kJ/mol',
        'ads_ads_coulomb_energy_unit': 'kJ/mol',
        'ads_ads_total_energy_average': -4.5501817208796655,
        'ads_ads_vdw_energy_average': -4.550181687621805,
        'ads_ads_coulomb_energy_average': 0.0,
        'ads_ads_total_energy_dev': 2.0057559085076093,
        'ads_ads_vdw_energy_dev': 2.0057559334510042,
        'ads_ads_coulomb_energy_dev': 0.0,
        'host_ads_total_energy_unit': 'kJ/mol',
        'host_ads_vdw_energy_unit': 'kJ/mol',
        'host_ads_coulomb_energy_unit': 'kJ/mol',
        'host_ads_total_energy_average': -174.60996722014394,
        'host_ads_vdw_energy_average': -174.60996720351505,
        'host_ads_coulomb_energy_average': 0.0,
        'host_ads_total_energy_dev': 34.12887304355653,
        'host_ads_vdw_energy_dev': 34.12887304355653,
        'host_ads_coulomb_energy_dev': 0.0,
        'total_energy_average': -21548.00707,
        'total_energy_unit': 'K',
        'total_energy_dev': 4309.35343
    }

    methane = {
        'mol_fraction': 1.0,
        'mol_fraction_unit': '-',
        'conversion_factor_molec_uc_to_mol_kg': 0.1866003989,
        'conversion_factor_molec_uc_to_mol_kg_unit': '(mol/kg)/(molec/uc)',
        'conversion_factor_molec_uc_to_gr_gr': 2.9935294361,
        'conversion_factor_molec_uc_to_gr_gr_unit': '(gr/gr)/(molec/uc)',
        'conversion_factor_molec_uc_to_cm3stp_gr': 4.1824568165,
        'conversion_factor_molec_uc_to_cm3stp_gr_unit': '(cm^3_STP/gr)/(molec/uc)',
        'conversion_factor_molec_uc_to_cm3stp_cm3': 3.095000393,
        'conversion_factor_molec_uc_to_cm3stp_cm3_unit': '(cm^3_STP/cm^3)/(molec/uc)',
        'partial_pressure': 500000.0,
        'partial_pressure_unit': 'Pa',
        'partial_fugacity': 494612.1383597442,
        'partial_fugacity_unit': 'Pa',
        'adsorbate_density_average': 26.62672,
        'adsorbate_density_unit': 'kg/m^3',
        'adsorbate_density_dev': 5.35266,
        'loading_absolute_average': 12.02,
        'loading_absolute_dev': 2.4163298616,
        'loading_absolute_unit': 'molecules/unit cell',
        'loading_excess_average': 11.02,
        'loading_excess_dev': 2.4163298616,
        'loading_excess_unit': 'molecules/unit cell',
        'widom_rosenbluth_factor_unit': '-',
        'widom_rosenbluth_factor_dev': 0.0,
        'widom_rosenbluth_factor_average': 0.0,
        'chemical_potential_unit': 'K',
        'chemical_potential_dev': 0.0,
        'chemical_potential_average': 0.0,
        'henry_coefficient_unit': 'mol/kg/Pa',
        'henry_coefficient_dev': 0.0,
        'henry_coefficient_average': 0.0
    }

    for key, value in general.items():
        assert value == parsed_parameters['general'][key]

    for key, value in methane.items():
        assert value == parsed_parameters['components']['methane'][key]


def test_parse_output_two_cmpnt():
    """Testing output parser on an output file with two components"""
    parsed_parameters = parse_base_output(os.path.join(CWD, "outputs/two_components.out"),
                                          system_name="system1",
                                          ncomponents=2)[0]
    general = {
        'exceeded_walltime': False,
        'framework_density': '0.000000000000',
        'framework_density_unit': 'kg/m^3',
        'temperature_average': None,
        'temperature_unit': 'K',
        'temperature_dev': None,
        'pressure_average': 0.0,
        'pressure_unit': 'Pa',
        'pressure_dev': 0.0,
        'cell_volume_average': 15625.0,
        'cell_volume_unit': 'A^3',
        'cell_volume_dev': 0.0,
        'box_ax_average': 25.0,
        'box_ax_unit': 'A^3',
        'box_ax_dev': 0.0,
        'box_by_average': 25.0,
        'box_by_unit': 'A^3',
        'box_by_dev': 0.0,
        'box_cz_average': 25.0,
        'box_cz_unit': 'A^3',
        'box_cz_dev': 0.0,
        'box_alpha_average': 90.0,
        'box_alpha_unit': 'degrees',
        'box_alpha_dev': 0.0,
        'box_beta_average': 90.0,
        'box_beta_unit': 'degrees',
        'box_beta_dev': 0.0,
        'box_gamma_average': 90.0,
        'box_gamma_unit': 'degrees',
        'box_gamma_dev': 0.0,
        'adsorbate_density_average': 4.40397,
        'adsorbate_density_unit': 'kg/m^3',
        'adsorbate_density_dev': 0.74921,
        'framework_heat_capacity_average': 32.79125,
        'framework_heat_capacity_unit': 'J/mol/K',
        'framework_heat_capacity_dev': 17.87762,
        'enthalpy_of_adsorption_average': 137.68727,
        'enthalpy_of_adsorption_unit': 'K',
        'enthalpy_of_adsorption_dev': 86.158033,
        'enthalpy_of_adsorption_total_molfrac_average': 151.20811,
        'enthalpy_of_adsorption_total_molfrac_unit': 'K',
        'enthalpy_of_adsorption_total_molfrac_dev': 79.043144,
        'ads_ads_total_energy_unit': 'kJ/mol',
        'ads_ads_vdw_energy_unit': 'kJ/mol',
        'ads_ads_coulomb_energy_unit': 'kJ/mol',
        'ads_ads_total_energy_average': -0.15252104334203112,
        'ads_ads_vdw_energy_average': -0.15252104334203112,
        'ads_ads_coulomb_energy_average': 0.0,
        'ads_ads_total_energy_dev': 0.16141328042825245,
        'ads_ads_vdw_energy_dev': 0.16141332200057704,
        'ads_ads_coulomb_energy_dev': 0.0,
        'host_ads_total_energy_unit': 'kJ/mol',
        'host_ads_vdw_energy_unit': 'kJ/mol',
        'host_ads_coulomb_energy_unit': 'kJ/mol',
        'host_ads_total_energy_average': 0.0,
        'host_ads_vdw_energy_average': 0.0,
        'host_ads_coulomb_energy_average': 0.0,
        'host_ads_total_energy_dev': 0.0,
        'host_ads_vdw_energy_dev': 0.0,
        'host_ads_coulomb_energy_dev': 0.0,
        'total_energy_average': 433.22727,
        'total_energy_unit': 'K',
        'total_energy_dev': 105.3826
    }

    propane = {
        'mol_fraction': 0.5,
        'mol_fraction_unit': '-',
        'conversion_factor_molec_uc_to_mol_kg': None,
        'conversion_factor_molec_uc_to_mol_kg_unit': '(mol/kg)/(molec/uc)',
        'conversion_factor_molec_uc_to_gr_gr': None,
        'conversion_factor_molec_uc_to_gr_gr_unit': '(gr/gr)/(molec/uc)',
        'conversion_factor_molec_uc_to_cm3stp_gr': None,
        'conversion_factor_molec_uc_to_cm3stp_gr_unit': '(cm^3_STP/gr)/(molec/uc)',
        'conversion_factor_molec_uc_to_cm3stp_cm3': 2.3820335839,
        'conversion_factor_molec_uc_to_cm3stp_cm3_unit': '(cm^3_STP/cm^3)/(molec/uc)',
        'partial_pressure': 250000.0,
        'partial_pressure_unit': 'Pa',
        'partial_fugacity': 230618.81828829306,
        'partial_fugacity_unit': 'Pa',
        'adsorbate_density_average': 3.97159,
        'adsorbate_density_unit': 'kg/m^3',
        'adsorbate_density_dev': 0.7045,
        'enthalpy_of_adsorption_average': 103.567,
        'enthalpy_of_adsorption_unit': 'K',
        'enthalpy_of_adsorption_dev': 98.162438,
        'loading_absolute_average': 0.8475,
        'loading_absolute_dev': 0.1503329638,
        'loading_absolute_unit': 'molecules/unit cell',
        'loading_excess_average': 0.8475,
        'loading_excess_dev': 0.1503329638,
        'loading_excess_unit': 'molecules/unit cell',
        'widom_rosenbluth_factor_unit': '-',
        'widom_rosenbluth_factor_dev': 0.0,
        'widom_rosenbluth_factor_average': 0.0,
        'chemical_potential_unit': 'K',
        'chemical_potential_dev': 0.0,
        'chemical_potential_average': 0.0,
        'henry_coefficient_unit': 'mol/kg/Pa',
        'henry_coefficient_dev': 0.0,
        'henry_coefficient_average': 0.0
    }

    butane = {
        'mol_fraction': 0.5,
        'mol_fraction_unit': '-',
        'conversion_factor_molec_uc_to_mol_kg': None,
        'conversion_factor_molec_uc_to_mol_kg_unit': '(mol/kg)/(molec/uc)',
        'conversion_factor_molec_uc_to_gr_gr': None,
        'conversion_factor_molec_uc_to_gr_gr_unit': '(gr/gr)/(molec/uc)',
        'conversion_factor_molec_uc_to_cm3stp_gr': None,
        'conversion_factor_molec_uc_to_cm3stp_gr_unit': '(cm^3_STP/gr)/(molec/uc)',
        'conversion_factor_molec_uc_to_cm3stp_cm3': 2.3820335839,
        'conversion_factor_molec_uc_to_cm3stp_cm3_unit': '(cm^3_STP/cm^3)/(molec/uc)',
        'partial_pressure': 250000.0,
        'partial_pressure_unit': 'Pa',
        'partial_fugacity': 121261.37081517381,
        'partial_fugacity_unit': 'Pa',
        'adsorbate_density_average': 0.43238,
        'adsorbate_density_unit': 'kg/m^3',
        'adsorbate_density_dev': 0.23112,
        'enthalpy_of_adsorption_average': 740.33952,
        'enthalpy_of_adsorption_unit': 'K',
        'enthalpy_of_adsorption_dev': 398.536954,
        'loading_absolute_average': 0.07,
        'loading_absolute_dev': 0.0374165739,
        'loading_absolute_unit': 'molecules/unit cell',
        'loading_excess_average': 0.07,
        'loading_excess_dev': 0.0374165739,
        'loading_excess_unit': 'molecules/unit cell',
        'widom_rosenbluth_factor_unit': '-',
        'widom_rosenbluth_factor_dev': 0.0,
        'widom_rosenbluth_factor_average': 0.0,
        'chemical_potential_unit': 'K',
        'chemical_potential_dev': 0.0,
        'chemical_potential_average': 0.0,
        'henry_coefficient_unit': 'mol/kg/Pa',
        'henry_coefficient_dev': 0.0,
        'henry_coefficient_average': 0.0
    }
    for key, value in general.items():
        assert value == parsed_parameters['general'][key]

    for key, value in propane.items():
        assert value == parsed_parameters['components']['propane'][key]

    for key, value in butane.items():
        assert value == parsed_parameters['components']['butane'][key]
