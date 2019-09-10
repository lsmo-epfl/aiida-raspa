"""
RaspaGEMCWorkChain : Rapspa workchain for GEMC calculation through RaspaBaseWorkChain
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

from aiida_raspa.utils.inspection_tools import (check_gemc_box, check_gemc_convergence)

ParameterData = DataFactory("dict")  #pylint: disable=invalid-name
FolderData = DataFactory('folder')  #pylint: disable=invalid-name
RaspaCalculation = CalculationFactory("raspa")  #pylint: disable=invalid-name


class RaspaGEMCWorkChain(WorkChain):
    """
    Handling the GEMC calculation through RaspaBaseWorkChain
    """

    _calculation_class = RaspaCalculation

    @classmethod
    def define(cls, spec):
        """
        Defining the class inputs.
        """
        super(RaspaGEMCWorkChain, cls).define(spec)

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
        self.ctx.boxes_size_ok = False

        # Getting the raspa parameters, copy them for further modification!
        self.ctx.parameters = deepcopy(self.ctx.inputs.raspa.parameters.get_dict())
        self.ctx.cutoff = self.ctx.parameters['GeneralSettings']['CutOff']

        # Getting the component name.
        self.ctx.comp_list = list(self.ctx.parameters['Component'].keys())

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
        Calculation should run until both simulation boxes provide valid
        sizes and also the error bar on number of molecules per simulation box
        falls below the requested value.
        """
        return not (self.ctx.converged and self.ctx.boxes_size_ok)

    def prepare_calculation(self):
        """
        Preparing and linking necessary inputs
        """
        if self.ctx.restart_calc is not None:
            self.ctx.inputs.raspa['retrieved_parent_folder'] = self.ctx.restart_calc

        self.ctx.inputs.raspa['parameters'] = Dict(dict=self.ctx.parameters).store()

    def run_calculation(self):
        """
        Run RASPA Calculation
        """
        running_base = self.submit(RaspaBaseWorkChain, **self.ctx.inputs)
        self.report("pk: {} | Submitted RaspaBaseWorkChain".format(running_base.pk))
        self.ctx.nruns += 1
        return ToContext(calculation=running_base)

    # pylint: disable=too-many-statements
    def inspect_calculation(self):
        """
        Inspecting the box lengths on each box
        Checking the convegence on each box
        """
        self.ctx.output_gemc = self.ctx.calculation.outputs.output_parameters.get_dict()
        # Box length check
        box_one_stat, box_two_stat = check_gemc_box(self.ctx.output_gemc, self.ctx.cutoff)
        box_one_size_ok = []
        box_two_size_ok = []

        # Check the box_one length.
        if not all(box_one_stat):
            self.report("<box_one> does not satisfy minimum image convention anymore!")

            length_string = self.ctx.inputs.raspa.parameters.get_dict()["System"]["box_one"]["BoxLengths"]
            box_length = []
            for element in length_string.split():
                try:
                    box_length.append(float(element))
                except ValueError:
                    pass
            # TODO: Make the box addition value smart. #pylint: disable=fixme
            # TODO: It can be taken from difference of initital and final size. #pylint: disable=fixme
            box_ax_new = box_length[0] + 2.0
            box_by_new = box_length[1] + 2.0
            box_cz_new = box_length[2] + 2.0
            self.report("inceasing the <box_one> dimenstion to {} {} {}".format(box_ax_new, box_by_new, box_cz_new))
            self.ctx.parameters["System"]["box_one"]["BoxLengths"] = "{} {} {}".format(
                box_ax_new, box_by_new, box_cz_new)

            box_one_size_ok.append(False)
        else:
            box_one_size_ok.append(True)

        if not all(box_two_stat):
            self.report("<box_two> does not satisfy minimum image convention anymore!")

            length_string = self.ctx.inputs.raspa.parameters.get_dict()["System"]["box_two"]["BoxLengths"]
            box_length = []
            for element in length_string.split():
                try:
                    box_length.append(float(element))
                except ValueError:
                    pass
            # TODO: Make the box addition value smart. #pylint: disable=fixme
            # TODO: It can be taken from difference of initital and final size. #pylint: disable=fixme
            box_ax_new = box_length[0] + 2.0
            box_by_new = box_length[1] + 2.0
            box_cz_new = box_length[2] + 2.0
            self.report("inceasing the <box_two> dimenstion to {} {} {}".format(box_ax_new, box_by_new, box_cz_new))
            self.ctx.parameters["System"]["box_two"]["BoxLengths"] = "{} {} {}".format(
                box_ax_new, box_by_new, box_cz_new)
            box_two_size_ok.append(False)
        else:
            box_two_size_ok.append(True)

        self.ctx.boxes_size_ok = all(box_one_size_ok) and all(box_two_size_ok)

        # Convergence check
        conv_stat = check_gemc_convergence(self.ctx.output_gemc, self.ctx.comp_list, self.ctx.conv_threshold)
        if not all(conv_stat):
            self.report("GEMC calculation is NOT converged: rastarting by increasing <NumberOfCycles>")
            self.ctx.restart_calc = self.ctx.calculation.outputs['retrieved']
            self.ctx.parameters["GeneralSettings"]["NumberOfCycles"] += self.ctx.additional_cycle
            self.ctx.parameters["GeneralSettings"]["NumberOfInitializationCycles"] += self.ctx.additional_cycle

            # RASPA reads the number of molecules from restart file!
            for comp in self.ctx.comp_list:
                self.ctx.parameters["Component"][comp]["CreateNumberOfMolecules"]["box_one"] = 0
                self.ctx.parameters["Component"][comp]["CreateNumberOfMolecules"]["box_two"] = 0
            ParameterData(dict=self.ctx.parameters).store()
            self.ctx.converged = False
        else:
            self.report("GEMC calculation is converged")
            self.ctx.converged = True

    def return_results(self):
        self.out('retrieved', self.ctx.calculation.outputs['retrieved'])
        self.out('output_parameters', self.ctx.calculation.outputs['output_parameters'])


# EOF
