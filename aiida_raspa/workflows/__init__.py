# -*- coding: utf-8 -*-
"""Base workflows for RASPA"""

from __future__ import print_function
from __future__ import absolute_import

from aiida.common.extendeddicts import AttributeDict
from aiida.work.run import submit
from aiida.work.workchain import WorkChain, Outputs
from aiida.orm.code import Code
from aiida.orm.utils import CalculationFactory, DataFactory
from aiida.work.workchain import ToContext, while_
import six

# data objects
CifData = DataFactory('cif')
FolderData = DataFactory('folder')
ParameterData = DataFactory('parameter')
SinglefileData = DataFactory('singlefile')

RaspaCalculation = CalculationFactory('raspa')

default_options = {
    "resources": {
        "num_machines": 1,
        "num_mpiprocs_per_machine": 1,
    },
    "max_wallclock_seconds": 1 * 60 * 60,
}


# pylint: disable=too-many-locals
def multiply_unit_cell(cif, threshold):
    """Resurns the multiplication factors (tuple of 3 int) for the cell vectors
    that are needed to respect: min(perpendicular_width) > threshold
    """
    from math import cos, sin, sqrt, pi
    import numpy as np
    deg2rad = pi / 180.

    struct = next(six.itervalues(cif.values.dictionary))

    a = float(struct['_cell_length_a'])
    b = float(struct['_cell_length_b'])
    c = float(struct['_cell_length_c'])

    alpha = float(struct['_cell_angle_alpha']) * deg2rad
    beta = float(struct['_cell_angle_beta']) * deg2rad
    gamma = float(struct['_cell_angle_gamma']) * deg2rad

    # first step is computing cell parameters according to  https://en.wikipedia.org/wiki/Fractional_coordinates
    # Note: this is the algorithm implemented in Raspa (framework.c/UnitCellBox). There also is a simpler one but it is less robust.
    v = sqrt(1 - cos(alpha)**2 - cos(beta)**2 - cos(gamma)**2 +
             2 * cos(alpha) * cos(beta) * cos(gamma))
    cell = np.zeros((3, 3))
    cell[0, :] = [a, 0, 0]
    cell[1, :] = [b * cos(gamma), b * sin(gamma), 0]
    cell[2, :] = [
        c * cos(beta),
        c * (cos(alpha) - cos(beta) * cos(gamma)) / (sin(gamma)),
        c * v / sin(gamma)
    ]
    cell = np.array(cell)

    # diagonalizing the cell matrix: note that the diagonal elements are the perpendicolar widths because ay=az=bz=0
    diag = np.diag(cell)
    return tuple(int(i) for i in np.ceil(threshold / diag * 2.))


class RaspaConvergeWorkChain(WorkChain):
    """A base workchain to get converged RASPA calculations"""

    @classmethod
    def define(cls, spec):
        super(RaspaConvergeWorkChain, cls).define(spec)

        spec.input('code', valid_type=Code)
        spec.input('structure', valid_type=CifData)
        spec.input("parameters", valid_type=ParameterData)
        spec.input(
            'retrieved_parent_folder',
            valid_type=FolderData,
            default=None,
            required=False)
        spec.input(
            'block_component_0',
            valid_type=SinglefileData,
            default=None,
            required=False)
        spec.input("_options", valid_type=dict, default=default_options)

        spec.outline(
            cls.setup,
            while_(cls.should_run_calculation)(
                cls.prepare_calculation,
                cls.run_calculation,
                cls.inspect_calculation,
            ),
            cls.return_results,
        )
        spec.output('retrieved_parent_folder', valid_type=FolderData)
        spec.output('component_0', valid_type=ParameterData)
        spec.output('output_parameters', valid_type=ParameterData)

    def setup(self):
        """Perform initial setup"""
        self.ctx.done = False
        self.ctx.nruns = 0
        self.ctx.structure = self.inputs.structure

        self.ctx.parameters = self.inputs.parameters.get_dict()

        # restard provided?
        try:
            self.ctx.restart_calc = self.inputs.retrieved_parent_folder
        except AttributeError:
            self.ctx.restart_calc = None

        # block pockets provided?
        try:
            self.ctx.block_component_0 = self.inputs.block_component_0
        except AttributeError:
            self.ctx.block_component_0 = None

        self.ctx.options = self.inputs._options  # pylint: disable=protected-access

    def should_run_calculation(self):
        return not self.ctx.done

    def prepare_calculation(self):
        """Prepare all the neccessary input links to run the calculation"""
        self.ctx.inputs = AttributeDict({
            'code': self.inputs.code,
            'structure': self.ctx.structure,
            '_options': self.ctx.options,
        })

        if self.ctx.restart_calc is not None:
            self.ctx.inputs['retrieved_parent_folder'] = self.ctx.restart_calc

        if self.ctx.block_component_0 is not None:
            self.ctx.inputs['block_component_0'] = self.ctx.block_component_0

        # Reading the CutOff, compute the UnitCells expansion
        cutoff = self.ctx.parameters['GeneralSettings']['CutOff']
        ucs = multiply_unit_cell(self.inputs.structure, cutoff)
        self.ctx.parameters['GeneralSettings'][
            'UnitCells'] = "{} {} {}".format(ucs[0], ucs[1], ucs[2])
        # use the new parameters
        p = ParameterData(dict=self.ctx.parameters)
        p.store()
        self.ctx.inputs['parameters'] = p

    def run_calculation(self):
        """Run raspa calculation."""
        # Create the calculation process and launch it
        process = RaspaCalculation.process()
        running = submit(process, **self.ctx.inputs)
        self.report("pk: {} | Running calculation with"
                    " RASPA".format(running.pid))
        self.ctx.nruns += 1
        return ToContext(calculation=Outputs(running))

    def inspect_calculation(self):
        """
        Analyse the results of CP2K calculation and decide weather there is a
        need to restart it. If yes, then decide exactly how to restart the
        calculation.
        """
        converged_mc = True
        self.ctx.restart_calc = self.ctx.calculation['retrieved']
        if converged_mc:
            self.report("Calculation converged, terminating the workflow")
            self.ctx.done = True

    def return_results(self):
        self.out('retrieved_parent_folder', self.ctx.restart_calc)
        # TODO: extend for the multi-component systems
        self.out('component_0', self.ctx.calculation['component_0'])
        self.out('output_parameters',
                 self.ctx.calculation['output_parameters'])
