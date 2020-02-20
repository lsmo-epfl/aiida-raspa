# -*- coding: utf-8 -*-
"""Base workchain to run a RASPA calculation"""

from aiida.common import AttributeDict
from aiida.engine import while_
from aiida.orm import Int
from aiida.plugins import CalculationFactory

from aiida_raspa.utils import ErrorHandlerReport, register_error_handler, add_write_binary_restart
from aiida_raspa.workchains.aiida_base_restart import BaseRestartWorkChain

RaspaCalculation = CalculationFactory('raspa')  # pylint: disable=invalid-name


class RaspaBaseWorkChain(BaseRestartWorkChain):
    """Workchain to run a RASPA calculation with automated error handling and restarts."""

    _calculation_class = RaspaCalculation

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(RaspaCalculation, namespace='raspa')
        spec.outline(
            cls.setup,
            while_(cls.should_run_calculation)(
                cls.run_calculation,
                cls.inspect_calculation,
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
        :param action: a string message with the action taken
        """
        arguments = [calculation.process_label, calculation.pk, calculation.exit_status, calculation.exit_message]
        self.report('{}<{}> failed with exit status {}: {}'.format(*arguments))
        self.report('Action taken: {}'.format(action))


@register_error_handler(RaspaBaseWorkChain, 570)
def _handle_timeout(self, calculation):
    """Error handler that restarts calculation finished with TIMEOUT ExitCode."""
    if calculation.exit_status == RaspaCalculation.spec().exit_codes.TIMEOUT.status:
        self.report_error_handled(calculation, "Timeout handler. Adding remote folder as input to use binary restart.")
        self.ctx.inputs.parent_folder = calculation.outputs.remote_folder

    return ErrorHandlerReport(True, False, None)
