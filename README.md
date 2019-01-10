[![PyPI version](https://badge.fury.io/py/aiida-raspa.svg)](https://badge.fury.io/py/aiida-raspa)

# aiida-raspa

[AiiDA](https://www.aiida.net) plugin for [RASPA2](https://github.com/numat/RASPA2).

## Installation

If you use ``pip``, you can install it as:
```
pip install aiida-raspa
```
If you want to install the plugin in an editable mode, run:
```
git clone https://github.com/yakutovicha/aiida-raspa
cd aiida-raspa
pip install -e .  # also installs aiida, if missing (but not postgres)
```
In case the plugin does not appear in `verdi calculation plugins` list, run 
```
reentry scan
```
and try again.


## Examples

See `examples` folder for complete examples of setting up a calculation or workflow.

simple calculation:
```shell
verdi daemon restart                                   # make sure the daemon is running
cd examples/simple_calculations
verdi run test_raspa_base.py <code_label> --submit     # submit test calculation
verdi calculation list -a -p1                          # check status of calculation
```
workflow:
```shell
verdi daemon restart                                   # make sure the daemon is running
cd examples/workflows
verdi run run_RaspaConverge_workflow.py  <code_label>  # submit test calculation
verdi work list -a -p1                                 # check status of calculation
```

## Analyzing output
```shell
$ verdi calculation show 7491
-----------  ------------------------------------
type         RaspaCalculation
pk           7491
uuid         adc178d9-9f7e-4bbf-8283-8768f1964d9a
label
description
ctime        2019-01-10 15:38:20.103794+00:00
mtime        2019-01-10 15:39:24.799300+00:00
computer     [3] deneb
code         raspa
-----------  ------------------------------------
##### INPUTS:
Link label      PK  Type
------------  ----  -------------
parameters    7490  ParameterData
structure     7489  CifData
##### OUTPUTS:
Link label           PK  Type
-----------------  ----  -------------
remote_folder      7492  RemoteData
retrieved          7498  FolderData
output_parameters  7499  ParameterData
component_0        7500  ParameterData
```
Results that are for the framework and adsorbate can be obtained:
```shell
$ verdi calculation res 7491 # same as $ verdi data parameter show 7499
{
  "ads_ads_coulomb_energy_average": 0.0, 
  "ads_ads_coulomb_energy_dev": 0.0, 
  "ads_ads_coulomb_energy_unit": "kJ/mol", 
  "ads_ads_total_energy_average": -4.4408682910929, 
  "ads_ads_total_energy_dev": 1.63152616602518, 
  "ads_ads_total_energy_unit": "kJ/mol", 
  "ads_ads_vdw_energy_average": -4.44086832435076, 
  "ads_ads_vdw_energy_dev": 1.63152614939625, 
  "ads_ads_vdw_energy_unit": "kJ/mol", 
  "adsorbate_density_average": 26.35203, 
  "adsorbate_density_dev": 4.63163, 
  "adsorbate_density_units": "kg/m^3", 
  "cell_volume_average": 12025.61229, 
  "cell_volume_dev": 0.0, 
  "cell_volume_units": "A^3", 
  "enthalpy_of_adsorption_average": -2092.24759, 
  "enthalpy_of_adsorption_dev": 315.039138, 
  "enthalpy_of_adsorption_units": "K", 
  "exceeded_walltime": false, 
  "framework_density": "739.995779685958", 
  "framework_density_units": "kg/m^3", 
  "framework_heat_capacity_average": 3082.15209, 
  "framework_heat_capacity_dev": 2889.16503, 
  "framework_heat_capacity_units": "J/mol/K", 
  "host_ads_coulomb_energy_average": 0.0, 
  "host_ads_coulomb_energy_dev": 0.0, 
  "host_ads_coulomb_energy_unit": "kJ/mol", 
  "host_ads_total_energy_average": -176.211538447682, 
  "host_ads_total_energy_dev": 36.0785945303337, 
  "host_ads_total_energy_unit": "kJ/mol", 
  "host_ads_vdw_energy_average": -176.211538455997, 
  "host_ads_vdw_energy_dev": 36.0785944970758, 
  "host_ads_vdw_energy_unit": "kJ/mol", 
  "pressure_average": 0.0, 
  "pressure_dev": 0.0, 
  "pressure_units": "Pa", 
  "temperature_average": 0.0, 
  "temperature_dev": 0.0, 
  "temperature_units": "K", 
  "total_energy_average": -21727.4844, 
  "total_energy_dev": 4526.71327, 
  "total_energy_units": "K"
}
```
Component specific results can be obtained:
```shell
$ verdi data parameter show 7499
{
  "ads_ads_coulomb_energy_average": 0.0, 
  "ads_ads_coulomb_energy_dev": 0.0, 
  "ads_ads_coulomb_energy_unit": "kJ/mol", 
  "ads_ads_total_energy_average": -4.4408682910929, 
  "ads_ads_total_energy_dev": 1.63152616602518, 
  "ads_ads_total_energy_unit": "kJ/mol", 
  "ads_ads_vdw_energy_average": -4.44086832435076, 
  "ads_ads_vdw_energy_dev": 1.63152614939625, 
  "ads_ads_vdw_energy_unit": "kJ/mol", 
  "adsorbate_density_average": 26.35203, 
  "adsorbate_density_dev": 4.63163, 
  "adsorbate_density_units": "kg/m^3", 
  "cell_volume_average": 12025.61229, 
  "cell_volume_dev": 0.0, 
  "cell_volume_units": "A^3", 
  "enthalpy_of_adsorption_average": -2092.24759, 
  "enthalpy_of_adsorption_dev": 315.039138, 
  "enthalpy_of_adsorption_units": "K", 
  "exceeded_walltime": false, 
  "framework_density": "739.995779685958", 
  "framework_density_units": "kg/m^3", 
  "framework_heat_capacity_average": 3082.15209, 
  "framework_heat_capacity_dev": 2889.16503, 
  "framework_heat_capacity_units": "J/mol/K", 
  "host_ads_coulomb_energy_average": 0.0, 
  "host_ads_coulomb_energy_dev": 0.0, 
  "host_ads_coulomb_energy_unit": "kJ/mol", 
  "host_ads_total_energy_average": -176.211538447682, 
  "host_ads_total_energy_dev": 36.0785945303337, 
  "host_ads_total_energy_unit": "kJ/mol", 
  "host_ads_vdw_energy_average": -176.211538455997, 
  "host_ads_vdw_energy_dev": 36.0785944970758, 
  "host_ads_vdw_energy_unit": "kJ/mol", 
  "pressure_average": 0.0, 
  "pressure_dev": 0.0, 
  "pressure_units": "Pa", 
  "temperature_average": 0.0, 
  "temperature_dev": 0.0, 
  "temperature_units": "K", 
  "total_energy_average": -21727.4844, 
  "total_energy_dev": 4526.71327, 
  "total_energy_units": "K"
}
```

Files that are downloaded by the plugin to the local machine:
```shell
$ verdi calculation outputls 7491
_scheduler-stderr.txt
_scheduler-stdout.txt
output_framework_1.1.1_300.000000_500000.data
restart_framework_1.1.1_300.000000_500000
```

Cat the output file:
```shell
$ verdi calculation outputcat 7491 -p output_framework_1.1.1_300.000000_500000.data
...
Average adsorption energy <U_gh>_1-<U_h>_0 obtained from Widom-insertion:
(Note: the total heat of adsorption is dH=<U_gh>_1-<U_h>_0 - <U_g> - RT)
=========================================================================

Simulation finished,  1 warnings
WARNING: INAPPROPRIATE NUMBER OF UNIT CELLS USED


Thu Jan 10 16:39:01 2019
Simulation finished on Thursday, January 10.
The end time was 04:39 PM.
```

## License

MIT

## Contact
yakutovicha@gmail.com
