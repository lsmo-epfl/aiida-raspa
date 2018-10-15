from __future__ import print_function


from aiida.work.workchain import WorkChain, Outputs
from aiida.orm.utils import CalculationFactory
RaspaCalculation = CalculationFactory('raspa')



def dict_merge(dct, merge_dct):
    """ Taken from https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
    Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    import collections
    for k, v in merge_dct.iteritems():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


class RaspaConvergeWorkChain(WorkChain):
    """A base workchain to get converged RASPA calculations"""
    @classmethod
    def define(cls, spec):
        super(RaspaBaseWorkChain, cls).define(spec)
        
        spec.input('code', valid_type=Code)
        spec.input('structure', valid_type=CifData)
        spec.input("parameters", valid_type=ParameterData,
                default=ParameterData(dict={}))
        spec.input("options", valid_type=ParameterData,
                default=ParameterData(dict=default_options))
        spec.input('parent_folder', valid_type=RemoteData,
                default=None, required=False)
        
        spec.outline(
            cls.setup,
            while_(cls.should_run_calculation)(
                cls.prepare_calculation,
                cls.run_calculation,
                cls.inspect_calculation,
            ),
            cls.return_results,
        )
        spec.output('remote_folder', valid_type=RemoteData)
    
    def setup(self):
        """Perform initial setup"""
        self.ctx.done = False
        self.ctx.nruns = 0
        self.ctx.structure = self.inputs.structure
        
        self.ctx.parameters = cp2k_default_parameters
        user_params = self.inputs.parameters.get_dict()
        dict_merge(self.ctx.parameters, user_params)
        
        self.ctx.options = self.inputs.options.get_dict()
    
    def should_run_calculation(self):
        return not self.ctx.done
    
    def prepare_calculation(self):
        """Prepare all the neccessary input links to run the calculation"""
        self.ctx.inputs = AttributeDict({
            'code': self.inputs.code,
            'structure'  : self.ctx.structure,
            '_options'    : self.ctx.options,
            })

        # use the new parameters
        p = ParameterData(dict=self.ctx.parameters)
        p.store()
        self.ctx.inputs['parameters'] = p
    
    def run_calculation(self): 
        """Run raspa calculation."""
        
        # Create the calculation process and launch it
        process = RaspaCalculation.process()
        future  = submit(process, **self.ctx.inputs)
        self.report("pk: {} | Running calculation with"
                " RASPA".format(future.pid))
        self.ctx.nruns += 1
        return ToContext(calculation=Outputs(future))

    def inspect_calculation(self):
        """
        Analyse the results of CP2K calculation and decide weather there is a
        need to restart it. If yes, then decide exactly how to restart the
        calculation.
        """
        converged_mc = True
        self.ctx.restart_calc = self.ctx.calculation['remote_folder']
        if converged_mc:
            self.report("Calculation converged, terminating the workflow")
            self.ctx.done = True

    def return_results(self):
        self.out('remote_folder', self.ctx.restart_calc)
