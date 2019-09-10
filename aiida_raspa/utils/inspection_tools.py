# -*- coding: utf-8 -*-
"""RASPA inspection tools"""


def check_widom_convergence(output_widom=None, comp_list=None, structure_label=None, conv_threshold=None):
    """
    Checks if a Widom particle insertion calculation is converged or not.
    Checking is based on the error bar on Henry coefficient.
    """
    conv_stat = []

    for comp in comp_list:
        kh_average_comp = output_widom[structure_label]["components"][comp]["henry_coefficient_average"]
        kh_dev_comp = output_widom[structure_label]["components"][comp]["henry_coefficient_dev"]

        error = round((kh_dev_comp / kh_average_comp), 2)
        if error <= conv_threshold:
            conv_stat.append(True)
        else:
            conv_stat.append(False)

    return conv_stat


def check_gcmc_convergence(output_gcmc=None, comp_list=None, structure_label=None, conv_threshold=None):
    """
    Checks if a GCMC calculation is converged or not.
    Checking is based on the error bar on average loading.
    """
    conv_stat = []

    for comp in comp_list:

        loading_average_comp = output_gcmc[structure_label]["components"][comp]["loading_absolute_average"]
        loading_dev_comp = output_gcmc[structure_label]["components"][comp]["loading_absolute_dev"]

        # TODO: It can happen for weekly adsorbed species. It is a temporary solution and #pylint: disable=fixme
        # we need to think about a better way to handle it.
        if loading_average_comp == 0:
            conv_stat.append(False)
        else:
            error = round((loading_dev_comp / loading_average_comp), 2)
            if error <= conv_threshold:
                conv_stat.append(True)
            else:
                conv_stat.append(False)
    return conv_stat


def check_gemc_convergence(output_gemc=None, comp_list=None, conv_threshold=None):
    """
    Checks if a GEMC calculation is converged or not.
    Checking is based on the error bar on average loading which is
    average number of molecules in each simulation box.
    """
    conv_stat = []

    for comp in comp_list:
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

    return conv_stat


# pylint: disable=too-many-branches
def check_gemc_box(output_gemc=None, cutoff=None):
    """
    Checks if each simulation box still satisfies minimum image convention
    condition or not.
    """
    box_one_stat = []
    box_two_stat = []

    for box in ["box_one", "box_two"]:
        if box == "box_one":
            if output_gemc["box_one"]["general"]["box_ax_average"] > 2 * cutoff:
                box_one_stat.append(True)
            else:
                box_one_stat.append(False)
            if output_gemc["box_one"]["general"]["box_by_average"] > 2 * cutoff:
                box_one_stat.append(True)
            else:
                box_one_stat.append(False)
            if output_gemc["box_one"]["general"]["box_cz_average"] > 2 * cutoff:
                box_one_stat.append(True)
            else:
                box_one_stat.append(False)

        if box == "box_two":
            if output_gemc["box_two"]["general"]["box_ax_average"] > 2 * cutoff:
                box_two_stat.append(True)
            else:
                box_two_stat.append(False)
            if output_gemc["box_two"]["general"]["box_by_average"] > 2 * cutoff:
                box_two_stat.append(True)
            else:
                box_two_stat.append(False)
            if output_gemc["box_two"]["general"]["box_cz_average"] > 2 * cutoff:
                box_two_stat.append(True)
            else:
                box_two_stat.append(False)

    return box_one_stat, box_two_stat
