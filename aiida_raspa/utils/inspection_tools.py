# -*- coding: utf-8 -*-
"""RASPA inspection tools"""

from aiida.engine import calcfunction
from aiida.orm import Dict


@calcfunction
def add_write_binary_restart(input_dict, write_every):
    final_dict = input_dict.get_dict()
    final_dict["GeneralSettings"]["WriteBinaryRestartFileEvery"] = write_every
    return input_dict if input_dict.get_dict() == final_dict else Dict(dict=final_dict)


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
