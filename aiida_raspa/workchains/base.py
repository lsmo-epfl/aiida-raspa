# -*- coding: utf-8 -*-
"""Base work chain to run a RASPA calculation"""

from aiida.common import AttributeDict
from aiida.engine import BaseRestartWorkChain, ProcessHandlerReport, process_handler, while_
from aiida.orm import Int, Str, Float
from aiida.plugins import CalculationFactory

from aiida_raspa.utils import add_write_binary_restart, modify_number_of_cycles, increase_box_lenght

RaspaCalculation = CalculationFactory('raspa')  # pylint: disable=invalid-name


class RaspaBaseWorkChain(BaseRestartWorkChain):
    """Workchain to run a RASPA calculation with automated error handling and restarts."""

    _process_class = RaspaCalculation

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(RaspaCalculation, namespace='raspa')
        spec.outline(
            cls.setup,
            while_(cls.should_run_process)(
                cls.run_process,
                cls.inspect_process,
            ),
            cls.results,
        )
        spec.expose_outputs(RaspaCalculation)

    def setup(self):
        """Call the `setup` of the `BaseRestartWorkChain` and then create the inputs dictionary in `self.ctx.inputs`.
        This `self.ctx.inputs` dictionary will be used by the `BaseRestartWorkChain` to submit the calculations in the
        internal loop."""

        super().setup()

        self.ctx.inputs = AttributeDict(self.exposed_inputs(RaspaCalculation, 'raspa'))
        if "WriteBinaryRestartFileEvery" not in self.ctx.inputs.parameters["GeneralSettings"]:
            self.ctx.inputs.parameters = add_write_binary_restart(self.ctx.inputs.parameters, Int(1000))

    def report_error_handled(self, calculation, action):
        """Report an action taken for a calculation that has failed.
        This should be called in a registered error handler if its condition is met and an action was taken.
        :param calculation: the failed calculation node
        :param action: a string message with the action taken"""

        arguments = [calculation.process_label, calculation.pk, calculation.exit_status, calculation.exit_message]
        self.report('{}<{}> failed with exit status {}: {}'.format(*arguments))
        self.report('Action taken: {}'.format(action))

    @process_handler(priority=570, exit_codes=RaspaCalculation.exit_codes.TIMEOUT, enabled=True)
    def handle_timeout(self, calculation):
        """Error handler that restarts calculation finished with TIMEOUT ExitCode."""
        self.report_error_handled(calculation, "Timeout handler. Adding remote folder as input to use binary restart.")
        self.ctx.inputs.parent_folder = calculation.outputs.remote_folder
        return ProcessHandlerReport(False)

    @process_handler(priority=400, enabled=False)
    def check_widom_convergence(self, calculation):
        """Checks whether a Widom particle insertion is converged. The check is based on the
        error bar of the Henry coefficient."""

        conv_threshold = 0.1
        additional_cycle = 2000

        output_widom = calculation.outputs.output_parameters.get_dict()
        structure_label = list(calculation.get_incoming().nested()['framework'].keys())[0]
        conv_stat = []

        for comp in calculation.inputs.parameters['Component']:
            kh_average_comp = output_widom[structure_label]["components"][comp]["henry_coefficient_average"]
            kh_dev_comp = output_widom[structure_label]["components"][comp]["henry_coefficient_dev"]

            error = round((kh_dev_comp / kh_average_comp), 2)
            if error <= conv_threshold:
                conv_stat.append(True)
            else:
                conv_stat.append(False)

        if not all(conv_stat):

            self.report("Widom particle insertion calculationulation is NOT converged: repeating with more trials...")
            self.ctx.inputs.retrieved_parent_folder = calculation.outputs['retrieved']
            self.ctx.inputs.parameters = modify_number_of_cycles(self.ctx.inputs.parameters,
                                                                 additional_init_cycle=Int(0),
                                                                 additional_prod_cycle=Int(additional_cycle))
            return ProcessHandlerReport(False)

        return None

    @process_handler(priority=410, enabled=False)
    def check_gcmc_convergence(self, calc):
        """Checks whether a GCMC calc is converged. Checking is based on the error bar on average loading."""
        conv_threshold = 0.1
        additional_init_cycle = 2000
        additional_prod_cycle = 2000

        output_gcmc = calc.outputs.output_parameters.get_dict()
        structure_label = list(calc.get_incoming().nested()['framework'].keys())[0]
        conv_stat = []

        for comp in calc.inputs.parameters['Component']:

            loading_average_comp = output_gcmc[structure_label]["components"][comp]["loading_absolute_average"]
            loading_dev_comp = output_gcmc[structure_label]["components"][comp]["loading_absolute_dev"]

            # It can happen for weekly adsorbed species.
            # we need to think about a better way to handle it.
            # Currently, if it happens for five iterations, self will not continue.
            if loading_average_comp == 0:
                conv_stat.append(False)
            else:
                error = round((loading_dev_comp / loading_average_comp), 2)
                if error <= conv_threshold:
                    conv_stat.append(True)
                else:
                    conv_stat.append(False)

        if not all(conv_stat):
            self.report("GCMC calculation is NOT converged: continuing from restart...")
            self.ctx.inputs.retrieved_parent_folder = calc.outputs['retrieved']
            self.ctx.inputs.parameters = modify_number_of_cycles(self.ctx.inputs.parameters,
                                                                 additional_init_cycle=Int(additional_init_cycle),
                                                                 additional_prod_cycle=Int(additional_prod_cycle))
            return ProcessHandlerReport(False)

        return None

    @process_handler(priority=410, enabled=False)
    def check_gemc_convergence(self, calc):
        """Checks whether a GEMC calc is converged. Checking is based on the error bar on average loading which is
        average number of molecules in each simulation box."""

        conv_threshold = 0.1
        additional_init_cycle = 2000
        additional_prod_cycle = 2000

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
            self.report("GEMC calculation is NOT converged: continuing from restart...")
            self.ctx.inputs.retrieved_parent_folder = calc.outputs['retrieved']
            self.ctx.inputs.parameters = modify_number_of_cycles(self.ctx.inputs.parameters,
                                                                 additional_init_cycle=Int(additional_init_cycle),
                                                                 additional_prod_cycle=Int(additional_prod_cycle))
            return ProcessHandlerReport(False)

        return None

    @process_handler(priority=400, enabled=False)
    def check_gemc_box(self, calc):
        """Checks whether each simulation box still satisfies minimum image convention."""

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
            self.report("GEMC box is NOT converged: repeating with increase box...")
            # Fixing the issue.
            if not all(box_one_stat):
                self.ctx.inputs.parameters = increase_box_lenght(self.ctx.inputs.parameters, Str("box_one"),
                                                                 Float(box_one_length_current[0]))

            if not all(box_two_stat):
                self.ctx.inputs.parameters = increase_box_lenght(self.ctx.inputs.parameters, Str("box_two"),
                                                                 Float(box_two_length_current[0]))

            return ProcessHandlerReport(True)

        return None
