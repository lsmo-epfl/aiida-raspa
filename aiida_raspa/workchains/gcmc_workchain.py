"""
RaspaGCMCWorkChain : Rapspa workchain for GCMC calculation through RaspaBaseWorkChain
"""
from __future__ import print_function
from __future__ import absolute_import
from copy import deepcopy

from aiida.common import AttributeDict
from aiida.plugins import CalculationFactory, DataFactory
from aiida.orm import Dict, Float, Int
from aiida.engine import submit  #pylint: disable=unused-import
from aiida.engine import ToContext, WorkChain, while_
from aiida_raspa.workchains import RaspaBaseWorkChain

from aiida_raspa.utils.multiply_unitcell import multiply_unit_cell
from aiida_raspa.utils.inspection_tools import check_gcmc_convergence

ParameterData = DataFactory("dict")  #pylint: disable=invalid-name
FolderData = DataFactory('folder')  #pylint: disable=invalid-name
RaspaCalculation = CalculationFactory("raspa")  #pylint: disable=invalid-name


class RaspaGCMCWorkChain(WorkChain):
    """
    Handling the GCMC calculation through RaspaBaseWorkChain
    """

    _calculation_class = RaspaCalculation

    @classmethod
    def define(cls, spec):
        """
        Defining the class inputs.
        """
        super(RaspaGCMCWorkChain, cls).define(spec)

        spec.expose_inputs(RaspaBaseWorkChain, namespace='raspa_base')

        spec.input('conv_threshold', valid_type=Float, required=True)
        spec.input('additional_cycle', valid_type=Int, required=True)

        # workflow
        spec.outline(
            cls.setup,
            while_(cls.should_run_calculation)(
                cls.prepare_calculation,
                cls.run_calculation,
                cls.inspect_calculation,
            ),
            cls.return_results,
        )

        spec.output('retrieved', valid_type=FolderData)
        spec.output('output_parameters', valid_type=ParameterData)

    def setup(self):
        """
        Initialization of workchain setup.
        """
        # Constructing input
        self.ctx.inputs = AttributeDict(self.exposed_inputs(RaspaBaseWorkChain, namespace='raspa_base'))

        # Setting run counter.
        self.ctx.nruns = 0
        self.ctx.converged = False

        # Getting the raspa parameters, copy them for further modification!
        self.ctx.parameters = deepcopy(self.ctx.inputs.raspa.parameters.get_dict())
        self.ctx.cutoff = self.ctx.parameters['GeneralSettings']['CutOff']

        # Getting the component name.
        self.ctx.comp_list = list(self.ctx.parameters['Component'].keys())

        # Getting structure and label only for widom and gcmc.
        self.ctx.structure_label = list(self.ctx.inputs.raspa['framework'].keys())[0]
        self.ctx.structure = self.ctx.inputs.raspa.framework[self.ctx.structure_label]

        # restard provided?
        try:
            self.ctx.restart_calc = self.ctx.inputs.raspa.retrieved_parent_folder
        except AttributeError:
            self.ctx.restart_calc = None

        # Setting up the convergence parameters.
        # TODO: Change the conv_threshold to a dictionary later. #pylint: disable=fixme
        # It will enhance the workchain and enabling it to assign
        # different conv_threshold for different components.
        self.ctx.conv_threshold = self.inputs.conv_threshold
        self.ctx.additional_cycle = self.inputs.additional_cycle

    def should_run_calculation(self):
        """
        Calculation should run until error bar on number of molecules per unit cell
        falls below the requested value for all components.
        """
        return not self.ctx.converged

    def prepare_calculation(self):
        """
        Preparing and linking necessary inputs
        """
        if self.ctx.restart_calc is not None:
            self.ctx.inputs.raspa['retrieved_parent_folder'] = self.ctx.restart_calc

        self.ctx.ucs = multiply_unit_cell(self.ctx.structure, self.ctx.cutoff * 2)
        self.ctx.parameters["System"][self.ctx.structure_label]["UnitCells"] = "{} {} {}".format(
            self.ctx.ucs[0], self.ctx.ucs[1], self.ctx.ucs[2])

        self.ctx.inputs.raspa['parameters'] = Dict(dict=self.ctx.parameters).store()

    def run_calculation(self):
        """
        Run RASPA Calculation
        """
        running_base = self.submit(RaspaBaseWorkChain, **self.ctx.inputs)
        self.report("pk: {} | Submitted RaspaBaseWorkChain".format(running_base.pk))
        self.ctx.nruns += 1
        return ToContext(calculation=running_base)

    def inspect_calculation(self):
        """
        Checking the convegence
        """
        self.ctx.output_gcmc = self.ctx.calculation.outputs.output_parameters.get_dict()
        conv_stat = check_gcmc_convergence(self.ctx.output_gcmc, self.ctx.comp_list, self.ctx.structure_label,
                                           self.ctx.conv_threshold)
        if not all(conv_stat):
            self.report("GCMC calculation is NOT converged: rastarting by increasing <NumberOfCycles>")
            self.ctx.restart_calc = self.ctx.calculation.outputs['retrieved']
            self.ctx.parameters["GeneralSettings"]["NumberOfCycles"] += self.ctx.additional_cycle
            self.ctx.parameters["GeneralSettings"]["NumberOfInitializationCycles"] += self.ctx.additional_cycle
            ParameterData(dict=self.ctx.parameters).store()
            self.ctx.converged = False
        else:
            self.report("GCMC calculation is converged")
            self.ctx.converged = True

    def return_results(self):
        self.out('retrieved', self.ctx.calculation.outputs['retrieved'])
        self.out('output_parameters', self.ctx.calculation.outputs['output_parameters'])


# EOF
