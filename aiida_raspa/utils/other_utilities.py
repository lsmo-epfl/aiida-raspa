# -*- coding: utf-8 -*-
"""Other utilities."""
from collections import namedtuple
from functools import wraps

from aiida.common import AiidaException, AttributeDict
from aiida.engine import ExitCode
from aiida.orm import Dict


class UnexpectedCalculationFailure(AiidaException):
    """Raised when a calculation job has failed for an unexpected or unrecognized reason."""


ErrorHandler = namedtuple('ErrorHandler', 'priority method')
"""A namedtuple to define an error handler for a :class:`~aiida.engine.processes.workchains.workchain.WorkChain`.
The priority determines in which order the error handling methods are executed, with
the higher priority being executed first. The method defines an unbound WorkChain method
that takes an instance of a :class:`~aiida.orm.CalcJobNode`
as its sole argument. If the condition of the error handler is met, it should return an :class:`.ErrorHandlerReport`.
:param priority: integer denoting the error handlers priority
:param method: the workchain class method
"""

ErrorHandlerReport = namedtuple('ErrorHandlerReport', 'is_handled do_break exit_code')
ErrorHandlerReport.__new__.__defaults__ = (False, False, ExitCode())
"""
A namedtuple to define an error handler report for a :class:`~aiida.engine.processes.workchains.workchain.WorkChain`.
This namedtuple should be returned by an error handling method of a workchain instance if
the condition of the error handling was met by the failure mode of the calculation.
If the error was appriopriately handled, the 'is_handled' field should be set to `True`,
and `False` otherwise. If no further error handling should be performed after this method
the 'do_break' field should be set to `True`
:param is_handled: boolean, set to `True` when an error was handled, default is `False`
:param do_break: boolean, set to `True` if no further error handling should be performed, default is `False`
:param exit_code: an instance of the :class:`~aiida.engine.processes.exit_code.ExitCode` tuple
"""


def prepare_process_inputs(process, inputs):
    """Prepare the inputs for submission for the given process, according to its spec.

    That is to say that when an input is found in the inputs that corresponds to an input port in the spec of the
    process that expects a `Dict`, yet the value in the inputs is a plain dictionary, the value will be wrapped in by
    the `Dict` class to create a valid input.

    :param process: sub class of `Process` for which to prepare the inputs dictionary
    :param inputs: a dictionary of inputs intended for submission of the process
    :return: a dictionary with all bare dictionaries wrapped in `Dict` if dictated by the process spec
    """
    prepared_inputs = wrap_bare_dict_inputs(process.spec().inputs, inputs)
    return AttributeDict(prepared_inputs)


def wrap_bare_dict_inputs(port_namespace, inputs):
    """Wrap bare dictionaries in `inputs` in a `Dict` node if dictated by the corresponding port in given namespace.

    :param port_namespace: a `PortNamespace`
    :param inputs: a dictionary of inputs intended for submission of the process
    :return: a dictionary with all bare dictionaries wrapped in `Dict` if dictated by the port namespace
    """
    from aiida.engine.processes import PortNamespace

    wrapped = {}

    for key, value in inputs.items():

        if key not in port_namespace:
            wrapped[key] = value
            continue

        port = port_namespace[key]

        if isinstance(port, PortNamespace):
            wrapped[key] = wrap_bare_dict_inputs(port, value)
        elif port.valid_type == Dict and isinstance(value, dict):
            wrapped[key] = Dict(dict=value)
        else:
            wrapped[key] = value

    return wrapped


def register_error_handler(cls, priority=None):
    """Decorate any function in an error handler :class:`.BaseRestartWorkChain` sub classes.

    The function expects two arguments, a workchain class and a priortity. The decorator will add the function as a
    class method to the workchain class and add an :class:`.ErrorHandler` tuple to the
    ``_error_handlers`` attribute of the workchain. During failed calculation handling the
    :meth:`.inspect_calculation` outline method will call the `_handle_calculation_failure` which will loop over all
    error handler in the ``_error_handlers``, sorted with respect to the priority in reverse.
    If the workchain class defines a :attr:`.BaseRestartWorkChain._verbose` attribute and is set to `True`, a report
    message will be fired when the error handler is executed.

    Requirements on the function signature of error handling functions.

    The function to which the decorator is applied needs to take two arguments:

        * `self`: This is the instance of the workchain itself
        * `calculation`: This is the calculation that failed and needs to be investigated

    The function body should usually consist of a single conditional that checks the calculation if
    the error that it is designed to handle is applicable. Although not required, it is advised that
    the function return an :class:`.ErrorHandlerReport` tuple when its conditional was met. If an error was handled
    it should set `is_handled` to `True`. If no other error handlers should be considered set `do_break` to `True`.

    :param cls: the workchain class to register the error handler with

    :param priority: optional integer that defines the order in which registered handlers will be called
        during the handling of a failed calculation. Higher priorities will be handled first. If the priority is `None`
        the handler will not be automatically called during calculation failure handling. This is useful to define
        handlers that one only wants to call manually, for example in the `_handle_sanity_checks` and still profit
        from the other features of this decorator.

    """

    def error_handler_decorator(handler):
        """Decorate a function to dynamically register an error handler to a `WorkChain` class."""

        @wraps(handler)
        def error_handler(self, calculation):
            """Wrap error handler to add a log to the report if the handler is called and verbosity is turned on."""
            if hasattr(cls, '_verbose') and cls._verbose:  # pylint: disable=protected-access
                if priority:
                    self.report('({}){}'.format(priority, handler.__name__))
                else:
                    self.report('{}'.format(handler.__name__))

            result = handler(self, calculation)

            # If a handler report is returned, attach the handler's name to node's attributes
            if isinstance(result, ErrorHandlerReport):
                try:
                    errors_handled = self.node.get_extra('errors_handled', [])
                    current_calculation = errors_handled[-1]
                except IndexError:
                    # The extra was never initialized, so we skip this functionality
                    pass
                else:
                    # Append the name of the handler to the last list in `errors_handled` and save it
                    current_calculation.append(handler.__name__)
                    self.node.set_extra('errors_handled', errors_handled)

            return result

        setattr(cls, handler.__name__, error_handler)

        if not hasattr(cls, '_error_handlers'):
            cls._error_handlers = []  # pylint: disable=protected-access
        cls._error_handlers.append(ErrorHandler(priority, error_handler))  # pylint: disable=protected-access

        return error_handler

    return error_handler_decorator
