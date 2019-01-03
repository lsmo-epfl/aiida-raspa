# -*- coding: utf-8 -*-
"""Raspa input plugin."""
from __future__ import absolute_import
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.exceptions import InputValidationError
from aiida.common.utils import classproperty
from aiida.orm.calculation.job import JobCalculation
from aiida.orm.utils import DataFactory
from six.moves import map
from six.moves import range
from shutil import copyfile

# data objects
CifData = DataFactory('cif')
FolderData = DataFactory('folder')
ParameterData = DataFactory('parameter')
RemoteData = DataFactory('remote')
SinglefileData = DataFactory('singlefile')


class RaspaCalculation(JobCalculation):
    """This is a RaspaCalculation, subclass of JobCalculation,
    to prepare input for an RaspaCalculation.
    For information on RASPA, refer to: https://github.com/numat/RASPA2.
    """

    # --------------------------------------------------------------------------
    def _init_internal_params(self):
        """
        Set parameters of instance
        """
        super(RaspaCalculation, self)._init_internal_params()
        self._INPUT_FILE_NAME = 'simulation.input'
        self._OUTPUT_FILE_NAME = 'Output/System_0/*'
        self._DEFAULT_INPUT_FILE = self._INPUT_FILE_NAME
        self._DEFAULT_OUTPUT_FILE = self._OUTPUT_FILE_NAME
        self._RESTART_FILE_NAME = 'Restart/System_0/restart*'
        self._PROJECT_NAME = 'aiida'
        self._COORDS_FILE_NAME = 'framework.cif'
        self._default_parser = 'raspa'

    # --------------------------------------------------------------------------
    @classproperty
    def _use_methods(cls):
        """
        Extend the parent _use_methods with further keys.
        This will be manually added to the _use_methods in each subclass
        """
        retdict = JobCalculation._use_methods
        retdict.update({
            "structure": {
                'valid_types': CifData,
                'additional_parameter': None,
                'linkname': 'structure',
                'docstring': "Choose the input structure to use",
            },
            "settings": {
                'valid_types': ParameterData,
                'additional_parameter': None,
                'linkname': 'settings',
                'docstring': "Use an additional node for special settings",
            },
            "parameters": {
                'valid_types':
                ParameterData,
                'additional_parameter':
                None,
                'linkname':
                'parameters',
                'docstring':
                "Use a node that specifies the "
                "input parameters for the namelists",
            },
            "parent_folder": {
                'valid_types':
                RemoteData,
                'additional_parameter':
                None,
                'linkname':
                'parent_folder',
                'docstring':
                "Use a remote folder as parent folder "
                "(for restarts and similar)",
            },
            # TODO: modify this for aiida version 1.0
            "block_component_0": {
                'valid_types': SinglefileData,
                'additional_parameter': None,
                'linkname': 'block_component_0',
                'docstring': "Use block pockets obtained with Zeo++ code",
            },
            "retrieved_parent_folder": {
                'valid_types':
                FolderData,
                'additional_parameter':
                None,
                'linkname':
                'retrieved_parent_folder',
                'docstring':
                "Use retrieved restart file for restart of this calculation",
            },
            "file": {
                'valid_types': SinglefileData,
                'additional_parameter': "linkname",
                'linkname': cls._get_linkname_file,
                'docstring': "Use files to provide additional parameters",
            },
        })
        return retdict

    # --------------------------------------------------------------------------
    @classmethod
    def _get_linkname_file(cls, linkname):
        return (linkname)

    # --------------------------------------------------------------------------
    # pylint: disable = too-many-locals
    def _prepare_for_submission(self, tempfolder, inputdict):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        :param inputdict: a dictionary with the input nodes, as they would
                be returned by get_inputdata_dict (without the Code!)
        """

        in_nodes = self._verify_inlinks(inputdict)
        params, structure, code, settings, block_pockets, restart_folder, local_copy_list = in_nodes

        # handle restart
        if restart_folder is not None:
            self._create_restart(restart_folder, params, tempfolder)

        # handle block pockets
        for i, block_pocket in enumerate(block_pockets):
            if block_pocket:
                params['Component'][i][
                    'BlockPocketsFileName'] = 'component_{}'.format(i)
                params['Component'][i]['BlockPockets'] = 'yes'
                copyfile(
                    block_pocket.get_file_abs_path(),
                    tempfolder.get_subfolder(".").get_abs_path(
                        'component_{}.block'.format(i)))

        # write raspa input file
        if 'FrameworkName' in params['GeneralSettings']:
            raise InputValidationError(
                'You should not provide "FrameworkName"'
                ' as an input parameter. It will be generated automatically'
                ' by AiiDA')
        elif structure is not None:
            params['GeneralSettings']['Framework'] = '0'
            params['GeneralSettings']['FrameworkName'] = 'framework'
        inp = RaspaInput(params)
        inp_fn = tempfolder.get_abs_path(self._INPUT_FILE_NAME)
        with open(inp_fn, "w") as f:
            f.write(inp.render())

        # create structure file
        if structure is not None:
            copyfile(structure.get_file_abs_path(),
                     tempfolder.get_abs_path(self._COORDS_FILE_NAME))

        # create code info
        codeinfo = CodeInfo()
        cmdline = settings.pop('cmdline', [])
        cmdline += [self._INPUT_FILE_NAME]
        codeinfo.cmdline_params = cmdline
        codeinfo.code_uuid = code.uuid

        # create calc info
        calcinfo = CalcInfo()
        calcinfo.stdin_name = self._INPUT_FILE_NAME
        calcinfo.uuid = self.uuid
        calcinfo.cmdline_params = codeinfo.cmdline_params
        calcinfo.stdin_name = self._INPUT_FILE_NAME
        #        calcinfo.stdout_name = self._OUTPUT_FILE_NAME
        calcinfo.codes_info = [codeinfo]

        # file lists
        calcinfo.remote_symlink_list = []
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [[self._OUTPUT_FILE_NAME, '.', 0],
                                  [self._RESTART_FILE_NAME, '.', 0]]
        calcinfo.retrieve_list += settings.pop('additional_retrieve_list', [])

        # check for left over settings
        if settings:
            msg = "The following keys have been found "
            msg += "in the settings input node {}, ".format(self.pk)
            msg += "but were not understood: " + ",".join(
                list(settings.keys()))
            raise InputValidationError(msg)

        return calcinfo

    # --------------------------------------------------------------------------
    def _create_restart(self, restart_folder, params, tempfolder):
        content = None
        for fname in restart_folder.get_folder_list():
            if "restart" in fname:
                content = restart_folder.get_file_content(fname)
        if content is None:
            raise InputValidationError(
                "Restart was requested but the restart"
                " file was not found in the previos calculation.")

        genset = params['GeneralSettings']
        (nx, ny, nz) = tuple(map(int, genset['UnitCells'].split()))
        restart_fname = "restart_%s_%d.%d.%d_%lf_%lg" % (
            "framework", nx, ny, nz, genset['ExternalTemperature'],
            genset['ExternalPressure'])
        fn = tempfolder.get_subfolder(
            'RestartInitial/System_0', create=True).get_abs_path(restart_fname)

        params['GeneralSettings']['RestartFile'] = True

        with open(fn, "w") as f:
            f.write(content)

    # --------------------------------------------------------------------------
    # pylint: disable=too-many-locals, too-many-branches
    def _verify_inlinks(self, inputdict):
        # parameters
        params_node = inputdict.pop('parameters', None)
        if params_node is None:
            raise InputValidationError("No parameters specified")
        if not isinstance(params_node, ParameterData):
            raise InputValidationError("parameters type not ParameterData")
        params = params_node.get_dict()

        try:
            n_components = len(params['Component'])
        except KeyError:
            raise InputValidationError(
                "Component section was not provided in the input parameters")

        # structure
        structure = inputdict.pop('structure', None)
        if structure is not None:
            if not isinstance(structure, CifData):
                raise InputValidationError("structure type not CifData")

        # code
        code = inputdict.pop(self.get_linkname('code'), None)
        if code is None:
            raise InputValidationError("No code specified")

        # settings
        # ... if not provided fall back to empty dict
        settings_node = inputdict.pop('settings', ParameterData())
        if not isinstance(settings_node, ParameterData):
            raise InputValidationError("settings type not ParameterData")
        settings = settings_node.get_dict()

        # block pockets
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

        # folder with the restart information
        restart_folder = inputdict.pop('retrieved_parent_folder', None)
        if restart_folder is not None and not isinstance(
                restart_folder, FolderData):
            raise InputValidationError(
                "retrieved parent folder is of type {}, "
                "but not FolderData".format(type(restart_folder)))

        # handle additional parameter files
        local_copy_list = []
        for k, v in inputdict.items():
            if isinstance(v, SinglefileData):
                inputdict.pop(k)
                local_copy_list.append((v.get_file_abs_path(), v.filename))

        if inputdict:
            msg = "unrecognized input nodes: " + str(list(inputdict.keys()))
            raise InputValidationError(msg)

        return (params, structure, code, settings, block_pockets,
                restart_folder, local_copy_list)


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
