# -*- coding: utf-8 -*-
"""Base workchain to run a RASPA calculation"""
from __future__ import absolute_import

from aiida.common import AttributeDict
from aiida.engine import while_
from aiida.plugins import CalculationFactory

from aiida_raspa.workchains.aiida_base_restart import BaseRestartWorkChain

RaspaCalculation = CalculationFactory('raspa')  # pylint: disable=invalid-name


class RaspaBaseWorkChain(BaseRestartWorkChain):
    """Workchain to run a RASPA calculation with automated error handling and restarts."""

    _calculation_class = RaspaCalculation

    @classmethod
    def define(cls, spec):
        super(RaspaBaseWorkChain, cls).define(spec)
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
        internal loop.
        """
        super(RaspaBaseWorkChain, self).setup()
        self.ctx.inputs = AttributeDict(self.exposed_inputs(RaspaCalculation, 'raspa'))
