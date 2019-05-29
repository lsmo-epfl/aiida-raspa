# -*- coding: utf-8 -*-
"""Raspa input plugin."""
from __future__ import absolute_import
from aiida.common import CalcInfo, CodeInfo, InputValidationError
from aiida.common.utils import classproperty
from aiida.engine import CalcJob
from aiida.plugins import DataFactory
from six.moves import map
from six.moves import range
from shutil import copyfile

# data objects
CifData = DataFactory('cif')
FolderData = DataFactory('folder')
ParameterData = DataFactory('dict')
RemoteData = DataFactory('remote')
SinglefileData = DataFactory('singlefile')


class RaspaCalculation(CalcJob):
    """This is a RaspaCalculation, subclass of JobCalculation,
    to prepare input for an RaspaCalculation.
    For information on RASPA, refer to: https://github.com/iraspa/raspa2.
    """
    # Defaults input and output files
    _INPUT_FILE_NAME = 'simulation.input'
    _OUTPUT_FILE_NAME = 'Output/System_0/*'
    #_DEFAULT_INPUT_FILE = self._INPUT_FILE_NAME
    #_DEFAULT_OUTPUT_FILE = self._OUTPUT_FILE_NAME
    _RESTART_FILE_NAME = 'Restart/System_0/restart*'
    _PROJECT_NAME = 'aiida'
    _COORDS_FILE_NAME = 'framework.cif'
    _DEFAULT_PARSER = 'raspa'

    @classmethod
    def define(cls, spec):
        super(RaspaCalculation, cls).define(spec)

        #Input parameters
        spec.input(
            'structure',
            valid_type=CifData,
            required=False,
            help='Input structure')
        spec.input(
            'settings',
            valid_type=ParameterData,
            required=False,
            help='additional input paramters')
        spec.input(
            'parameters',
            valid_type=ParameterData,
            required=False,
            help='the input parameters')
        spec.input(
            'parent_calc_folder',
            valid_type=RemoteData,
            required=False,
            help='use a remote folder as parent folder')
        spec.input(
            'block_component_0',
            valid_type=SinglefileData,
            required=False,
            help='Zeo++ block file')
        spec.input(
            'retrived_parent_folder',
            valid_type=FolderData,
            required=False,
            help='For restarting the calculation')
        spec.input(
            'file',
            valid_type=SinglefileData,
            required=False,
            help='additiona input file',
            dynamic=True)

        #TODO: Adding the defaults and outputs;

        spec.output(
            'results',
            valid_type=Dict,
            required=True,
            help='The results of calculation')
        spec.output(
            'structure',
            valid_type=StructureData,
            required=False,
            help='Structure with adsorbate')
        spec.default_output_node = 'results'

    # --------------------------------------------------------------------------
    #@classmethod
    #def _get_linkname_file(cls, linkname):
    #    return (linkname)

    # --------------------------------------------------------------------------
    # pylint: disable = too-many-locals
    def prepare_for_submission(self, folder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param folder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        """

        #This needs to be double checked.
        if 'structure' in self.inputs:
            self.inputs.structure.export(
                folder.get_abs_path(self._DEFAULT_INPUT_FILE),
                fileformat='cif')

        # handle restart
        if 'restart_folder' is not None:
            self._create_restart(folder)

        if 'parameters' in self.inputs:
            parameters_dict = self.inputs.parameters.get_dict()

        restart_folder = inputdict.pop('retrieved_parent_folder', None)
        if restart_folder is not None and not isinstance(
                restart_folder, FolderData):
            raise InputValidationError(
                "retrieved parent folder is of type {}, "
                "but not FolderData".format(type(restart_folder)))

        # handle block pockets
        # This part needs to be reformulated.

        for i, block_pocket in enumerate('block_pockets'):
            if block_pocket:
                parameters_dict['Component'][i][
                    'BlockPocketsFileName'] = 'component_{}'.format(i)
                parameters_dict['Component'][i]['BlockPockets'] = 'yes'
                copyfile(
                    block_pocket.get_file_abs_path(),
                    folder.get_subfolder(".").get_abs_path(
                        'component_{}.block'.format(i)))

        block_pockets = []
        for i in range(n_components):
            bp = inputdict.pop('block_component_{}'.format(i), None)
            if bp:
                if isinstance(bp, SinglefileData):
                    block_pockets.append(bp)
                else:
                    raise InputValidationError(
                        "Block pockets should be either None, or of the type SinglefileData."
                        "You provided the object {} of type {}".format(
                            bp, type(bp)))
            else:
                block_pockets.append(None)

        # write raspa input file
        if 'FrameworkName' in self.input(['GeneralSettings']):
            raise InputValidationError(
                'You should not provide "FrameworkName"'
                ' as an input parameter. It will be generated automatically'
                ' by AiiDA')
        elif 'structure' is not None:
            parameters_dict['GeneralSettings']['Framework'] = '0'
            parameters_dict['GeneralSettings']['FrameworkName'] = 'framework'
        inp = RaspaInput(self.inputs.parameters.get_dict())
        inp_fn = folder.get_abs_path(self._INPUT_FILE_NAME)
        with open(inp_fn, "w") as f:
            f.write(inp.render())

        #This needs to be doubel checked and verfied.
        if 'setting' in self.inputs:
            settings = self.inputs.settings.get_dict()
        else:
            settings = {}

        # create structure file
        if 'structure' is not None:
            copyfile(structure.get_file_abs_path(),
                     folder.get_abs_path(self._COORDS_FILE_NAME))

        # create code info
        codeinfo = CodeInfo()
        codeinfo.cmdline_params = settings.pop(
            'cmdline', []) + ["-i", self._DEFAULT_INPUT_FILE]
        codeinfo.stdout_name = self._DEFAULT_OUTPUT_FILE
        codeinfo.code_uuid = self.inputs.code.uuid

        # create calc info
        calcinfo = CalcInfo()
        calcinfo.stdin_name = self._DEFAULT_INPUT_FILE
        calcinfo.uuid = self.uuid
        calcinfo.cmdline_params = codeinfo.cmdline_params
        calcinfo.stdin_name = self._DEFAULT_INPUT_FILE
        calcinfo.stdout_name = self._DEFAULT_OUTPUT_FILE
        calcinfo.codes_info = [codeinfo]

        # file lists
        calcinfo.remote_symlink_list = []
        calcinfo.local_copy_list = local_copy_list
        if 'file' in self.inputs:
            calcinfo.local_copy_list = []
            for fobj in self.inputs.file.values():
                calcinfo.local_copy_list.append((fobj.uuid, fobj.filename,
                                                 fobj.filename))
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [[self._DEFAULT_OUTPUT_FILE, '.', 0],
                                  [self._DEFAULT_RESTART_FILE_NAME, '.', 0]]
        calcinfo.retrieve_list += settings.pop('additional_retrieve_list', [])

        # check for left over settings
        if settings:
            raise InputValidationError(
                "The following keys have been found " +
                "in the settings input node {}, ".format(self.pk) +
                "but were not understood: " + ",".join(list(settings.keys())))

#        if settings:
#            msg = "The following keys have been found "
#            msg += "in the settings input node {}, ".format(self.pk)
#            msg += "but were not understood: " + ",".join(list(
#                settings.keys()))
#            raise InputValidationError(msg)

        return calcinfo

    # --------------------------------------------------------------------------
    def _create_restart(self, folder):
        content = None
        for fname in restart_folder.get_folder_list():
            if "restart" in fname:
                content = restart_folder.get_file_content(fname)
        if content is None:
            raise InputValidationError(
                "Restart was requested but the restart"
                " file was not found in the previos calculation.")

        genset = self.input(['GeneralSettings'])
        (nx, ny, nz) = tuple(map(int, genset['UnitCells'].split()))
        restart_fname = "restart_%s_%d.%d.%d_%lf_%lg" % (
            "framework", nx, ny, nz, genset['ExternalTemperature'],
            genset['ExternalPressure'])
        fn = folder.get_subfolder(
            'RestartInitial/System_0', create=True).get_abs_path(restart_fname)

        self.input['GeneralSettings']['RestartFile'] = True

        with open(fn, "w") as f:
            f.write(content)

    # --------------------------------------------------------------------------
    # pylint: disable=too-many-locals, too-many-branches
    #def _verify_inlinks(self, inputdict):
    # parameters
    #    params_node = inputdict.pop('parameters', None)
    #    if params_node is None:
    #        raise InputValidationError("No parameters specified")
    #    if not isinstance(params_node, ParameterData):
    #        raise InputValidationError("parameters type not ParameterData")
    #    params = params_node.get_dict()

        try:
            n_components = len(params['Component'])
        except KeyError:
            raise InputValidationError(
                "Component section was not provided in the input parameters")

        # structure
        #structure = inputdict.pop('structure', None)
        #if structure is not None:
        #    if not isinstance(structure, CifData):
        #        raise InputValidationError("structure type not CifData")

        # code
        #code = inputdict.pop(self.get_linkname('code'), None)
        #if code is None:
        #    raise InputValidationError("No code specified")

        # settings
        # ... if not provided fall back to empty dict
        #settings_node = inputdict.pop('settings', Dict())
        #if not isinstance(settings_node, ParameterData):
        #    raise InputValidationError("settings type not ParameterData")
        #settings = settings_node.get_dict()

        # block pockets

        # folder with the restart information

        # handle additional parameter files
        #local_copy_list = []
        #for k, v in inputdict.items():
        #    if isinstance(v, SinglefileData):
        #        inputdict.pop(k)
        #        local_copy_list.append((v.get_file_abs_path(), v.filename))

        #if inputdict:
        #    msg = "unrecognized input nodes: " + str(list(inputdict.keys()))
        #    raise InputValidationError(msg)

        #return (params, structure, code, settings, block_pockets,
        #        restart_folder, local_copy_list)


# ==============================================================================
class RaspaInput(object):
    def __init__(self, params):
        self.params = params

    # --------------------------------------------------------------------------
    def render(self):
        output = ["!!! Generated by AiiDA !!!"]
        section = self.params.pop("GeneralSettings")
        self._render_section(output, section)

        section = self.params.pop("Component")
        for i, molec in enumerate(section):
            output.append('Component %d MoleculeName %s' %
                          (i, molec.pop("MoleculeName")))
            self._render_section(output, molec, indent=3)
        return "\n".join(output)

    # --------------------------------------------------------------------------
    def _render_section(self, output, params, indent=0):
        """
        It takes a dictionary and recurses through.

        For key-value pair it checks whether the value is a dictionary
        and prepends the key with &
        It passes the valued to the same function, increasing the indentation
        If the value is a list, I assume that this is something the user
        wants to store repetitively
        """
        #        output.append("enter")
        #        output.append("This what comes:" + str(params))
        for key, val in sorted(params.items()):
            if isinstance(val, list):
                output.append('%s%s  %s' % (' ' * indent, key, ' '.join(
                    str(p) for p in val)))
            elif isinstance(val, bool):
                val_str = 'yes' if val else 'no'
                output.append('%s%s  %s' % (' ' * indent, key, val_str))
            else:
                output.append('%s%s  %s' % (' ' * indent, key, val))


#        output.append('exit')
# EOF
