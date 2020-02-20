# -*- coding: utf-8 -*-
"""RASPA inspection tools"""

from aiida.engine import calcfunction
from aiida.orm import Dict, Int, Str, Float

from .other_utilities import ErrorHandlerReport


@calcfunction
def add_write_binary_restart(input_dict, write_every):
    final_dict = input_dict.get_dict()
    final_dict["GeneralSettings"]["WriteBinaryRestartFileEvery"] = write_every
    return input_dict if input_dict.get_dict() == final_dict else Dict(dict=final_dict)


@calcfunction
def modify_number_of_cycles(input_dict, additional_init_cycle, additional_prod_cycle):
    """Modify number of cycles to improve the convergence."""
    final_dict = input_dict.get_dict()
    try:
        final_dict["GeneralSettings"]["NumberOfInitializationCycles"] += additional_init_cycle.value
    except KeyError:
        final_dict["GeneralSettings"]["NumberOfInitializationCycles"] = additional_init_cycle.value

    final_dict["GeneralSettings"]["NumberOfCycles"] += additional_prod_cycle.value

    # It is a restart job the number of molecules need to be set to zero
    for component in final_dict['Component'].values():
        if "CreateNumberOfMolecules" in component:
            if isinstance(component["CreateNumberOfMolecules"], dict):
                for number in component["CreateNumberOfMolecules"]:
                    component["CreateNumberOfMolecules"][number] = 0
            else:
                component["CreateNumberOfMolecules"] = 0

    # Return final_dict dict only if it was modified
    return input_dict if input_dict.get_dict() == final_dict else Dict(dict=final_dict)


@calcfunction
def increase_box_lenght(input_dict, box_name, box_length_current):
    """Increase the box lenght to improve the convegence."""
    import math

    final_dict = input_dict.get_dict()
    bx_length_old = [float(element) for element in final_dict["System"][box_name.value]["BoxLengths"].split()]

    # We do the simulation in cubic box.
    addition_length = abs(math.ceil(bx_length_old[0] - box_length_current.value))
    box_one_length_new = [bx_length_old[i] + addition_length for i in range(3)]
    final_dict["System"][box_name.value]["BoxLengths"] = "{} {} {}".format(*box_one_length_new)

    return Dict(dict=final_dict)


def check_widom_convergence(workchain, calc, conv_threshold=0.1, additional_cycle=0):
    """
    Checks whether a Widom particle insertion is converged.
    Checking is based on the error bar on Henry coefficient.
    """
    output_widom = calc.outputs.output_parameters.get_dict()
    structure_label = list(calc.get_incoming().nested()['framework'].keys())[0]
    conv_stat = []

    for comp in calc.inputs.parameters['Component']:
        kh_average_comp = output_widom[structure_label]["components"][comp]["henry_coefficient_average"]
        kh_dev_comp = output_widom[structure_label]["components"][comp]["henry_coefficient_dev"]

        error = round((kh_dev_comp / kh_average_comp), 2)
        if error <= conv_threshold:
            conv_stat.append(True)
        else:
            conv_stat.append(False)

    if not all(conv_stat):
        workchain.report("Widom particle insertion calculation is NOT converged: repeating with more trials...")
        workchain.ctx.inputs.retrieved_parent_folder = calc.outputs['retrieved']
        workchain.ctx.inputs.parameters = modify_number_of_cycles(workchain.ctx.inputs.parameters,
                                                                  additional_init_cycle=Int(0),
                                                                  additional_prod_cycle=Int(additional_cycle))
        return ErrorHandlerReport(True, False)

    return None


def check_gcmc_convergence(workchain, calc, conv_threshold=0.1, additional_init_cycle=0, additional_prod_cycle=0):
    """
    Checks whether a GCMC calc is converged.
    Checking is based on the error bar on average loading.
    """
    output_gcmc = calc.outputs.output_parameters.get_dict()
    structure_label = list(calc.get_incoming().nested()['framework'].keys())[0]
    conv_stat = []

    for comp in calc.inputs.parameters['Component']:

        loading_average_comp = output_gcmc[structure_label]["components"][comp]["loading_absolute_average"]
        loading_dev_comp = output_gcmc[structure_label]["components"][comp]["loading_absolute_dev"]

        # It can happen for weekly adsorbed species.
        # we need to think about a better way to handle it.
        # Currently, if it happens for five iterations, workchain will not continue.
        if loading_average_comp == 0:
            conv_stat.append(False)
        else:
            error = round((loading_dev_comp / loading_average_comp), 2)
            if error <= conv_threshold:
                conv_stat.append(True)
            else:
                conv_stat.append(False)

    if not all(conv_stat):
        workchain.report("GCMC calculation is NOT converged: continuing from restart...")
        workchain.ctx.inputs.retrieved_parent_folder = calc.outputs['retrieved']
        workchain.ctx.inputs.parameters = modify_number_of_cycles(workchain.ctx.inputs.parameters,
                                                                  additional_init_cycle=Int(additional_init_cycle),
                                                                  additional_prod_cycle=Int(additional_prod_cycle))
        return ErrorHandlerReport(True, False)

    return None


def check_gemc_convergence(workchain, calc, conv_threshold=0.1, additional_init_cycle=0, additional_prod_cycle=0):
    """
    Checks whether a GCMC calc is converged.
    Checking is based on the error bar on average loading which is
    average number of molecules in each simulation box.
    """
    output_gemc = calc.outputs.output_parameters.get_dict()
    conv_stat = []

    for comp in calc.inputs.parameters['Component']:
        molec_per_box1_comp_average = output_gemc['box_one']["components"][comp]["loading_absolute_average"]
        molec_per_box2_comp_average = output_gemc['box_two']["components"][comp]["loading_absolute_average"]
        molec_per_box1_comp_dev = output_gemc['box_one']["components"][comp]["loading_absolute_dev"]
        molec_per_box2_comp_dev = output_gemc['box_two']["components"][comp]["loading_absolute_dev"]

        error_box1 = round((molec_per_box1_comp_dev / molec_per_box1_comp_average), 2)
        error_box2 = round((molec_per_box2_comp_dev / molec_per_box2_comp_average), 2)

        if (error_box1 <= conv_threshold) and (error_box2 <= conv_threshold):
            conv_stat.append(True)
        else:
            conv_stat.append(False)

    if not all(conv_stat):
        workchain.report("GEMC calculation is NOT converged: continuing from restart...")
        workchain.ctx.inputs.retrieved_parent_folder = calc.outputs['retrieved']
        workchain.ctx.inputs.parameters = modify_number_of_cycles(workchain.ctx.inputs.parameters,
                                                                  additional_init_cycle=Int(additional_init_cycle),
                                                                  additional_prod_cycle=Int(additional_prod_cycle))
        return ErrorHandlerReport(True, False)

    return None


def check_gemc_box(workchain, calc):
    """
    Checks whether each simulation box still satisfies minimum image convention.
    """
    output_gemc = calc.outputs.output_parameters.get_dict()
    cutoff = calc.inputs.parameters['GeneralSettings']['CutOff']
    box_one_stat = []
    box_two_stat = []

    box_one_length_current = []
    box_two_length_current = []

    for box_len_ave in ["box_ax_average", "box_by_average", "box_cz_average"]:
        if output_gemc["box_one"]["general"][box_len_ave] > 2 * cutoff:
            box_one_stat.append(True)
        else:
            box_one_stat.append(False)
            box_one_length_current.append(output_gemc["box_one"]["general"][box_len_ave])

        if output_gemc["box_two"]["general"][box_len_ave] > 2 * cutoff:
            box_two_stat.append(True)
        else:
            box_two_stat.append(False)
            box_two_length_current.append(output_gemc["box_two"]["general"][box_len_ave])

    if not all(box_one_stat and box_two_stat):
        workchain.report("GEMC box is NOT converged: repeating with increase box...")
        # Fixing the issue.
        if not all(box_one_stat):
            workchain.ctx.inputs.parameters = increase_box_lenght(workchain.ctx.inputs.parameters, Str("box_one"),
                                                                  Float(box_one_length_current[0]))

        if not all(box_two_stat):
            workchain.ctx.inputs.parameters = increase_box_lenght(workchain.ctx.inputs.parameters, Str("box_two"),
                                                                  Float(box_two_length_current[0]))

        return ErrorHandlerReport(True, False)

    return None
