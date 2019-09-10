# -*- coding: utf-8 -*-
"""Unit cell multiplication"""
from __future__ import absolute_import
from math import cos, sin, sqrt, pi, fabs, ceil
import six
import numpy as np


# pylint: disable=too-many-locals
def multiply_unit_cell(cif, threshold):
    """Returns the multiplication factors (tuple of 3 int) for the cell vectors
    to respect, in every direction: min(perpendicular_width) > threshold
    """

    deg2rad = pi / 180.

    # Parsing cif
    struct = next(six.itervalues(cif.values.dictionary))

    a = float(struct['_cell_length_a'])  # pylint: disable=invalid-name
    b = float(struct['_cell_length_b'])  # pylint: disable=invalid-name
    c = float(struct['_cell_length_c'])  # pylint: disable=invalid-name

    alpha = float(struct['_cell_angle_alpha']) * deg2rad
    beta = float(struct['_cell_angle_beta']) * deg2rad
    gamma = float(struct['_cell_angle_gamma']) * deg2rad

    # first step is computing cell parameters according to  https://en.wikipedia.org/wiki/Fractional_coordinates
    # Note: this is the algorithm implemented in Raspa (framework.c/UnitCellBox). There also is a simpler one but
    # it is less robust.
    val = sqrt(1 - cos(alpha)**2 - cos(beta)**2 - cos(gamma)**2 + 2 * cos(alpha) * cos(beta) * cos(gamma))
    cell = np.zeros((3, 3))
    cell[0, :] = [a, 0, 0]
    cell[1, :] = [b * cos(gamma), b * sin(gamma), 0]
    cell[2, :] = [c * cos(beta), c * (cos(alpha) - cos(beta) * cos(gamma)) / (sin(gamma)), c * val / sin(gamma)]
    cell = np.array(cell)

    # Computing perpendicular widths, as implemented in Raspa
    # for the check (simplified for triangular cell matrix)
    axc1 = cell[0, 0] * cell[2, 2]
    axc2 = -cell[0, 0] * cell[2, 1]
    bxc1 = cell[1, 1] * cell[2, 2]
    bxc2 = -cell[1, 0] * cell[2, 2]
    bxc3 = cell[1, 0] * cell[2, 1] - cell[1, 1] * cell[2, 0]
    det = fabs(cell[0, 0] * cell[1, 1] * cell[2, 2])
    perpwidth = np.zeros(3)
    perpwidth[0] = det / sqrt(bxc1**2 + bxc2**2 + bxc3**2)
    perpwidth[1] = det / sqrt(axc1**2 + axc2**2)
    perpwidth[2] = cell[2, 2]

    return tuple(int(ceil(threshold / perpwidth[i])) for i in six.moves.range(3))
