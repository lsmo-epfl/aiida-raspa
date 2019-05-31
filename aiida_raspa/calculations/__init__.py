# -*- coding: utf-8 -*-
"""Raspa input plugin."""
from __future__ import absolute_import
from shutil import copyfile
import six
from six.moves import map, range

from aiida.orm import Dict, FolderData, RemoteData, SinglefileData
from aiida.common import CalcInfo, CodeInfo, InputValidationError
from aiida.engine import CalcJob
from aiida.plugins import DataFactory

# data objects
CifData = DataFactory('cif')  # pylint: disable=invalid-name
StructureData = DataFactory('structure')  # pylint: disable=invalid-name


class RaspaCalculation(CalcJob):
    """This is a RaspaCalculation, subclass of CalcJob, to prepare input for RASPA code.
    For information on RASPA, refer to: https://github.com/iraspa/raspa2.
    """
    # Defaults
    INPUT_FILE = 'simulation.input'
    OUTPUT_FILE = 'Output/System_0/*'
    RESTART_FILE = 'Restart/System_0/restart*'
    PROJECT_NAME = 'aiida'
    COORDS_FILE = 'framework.cif'
    DEFAULT_PARSER = 'raspa'

    @classmethod
    def define(cls, spec):
        super(RaspaCalculation, cls).define(spec)

        #Input parameters
        spec.input('parameters', valid_type=Dict, required=True, help='Input parameters')
        spec.input('structure', valid_type=CifData, required=False, help='Input structure')
        # do `settings` need to be of type `Dict`? Would dict also work?
        spec.input('settings', valid_type=Dict, required=False, help='Additional input parameters')
        spec.input('parent_calc_folder', valid_type=RemoteData, required=False, help='Remote folder used for restarts')
        spec.input('block_component_0', valid_type=SinglefileData, required=False, help='Zeo++ block file')
        spec.input(
            'retrived_parent_folder', valid_type=FolderData, required=False, help='For restarting the calculation')
        spec.input('file', valid_type=SinglefileData, required=False, help='additiona input file')

        spec.input('metadata.options.parser_name', valid_type=six.string_types, default=cls.DEFAULT_PARSER, non_db=True)

        # Output parameters
        spec.outputs.dynamic = True
        spec.output('output_parameters', valid_type=Dict, required=True, help='The results of calculation')
        spec.default_output_node = 'output_parameters'

    # --------------------------------------------------------------------------
    # pylint: disable = too-many-locals
    def prepare_for_submission(self, folder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param folder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        """

        # handle input parameters
        parameters = self.inputs.parameters.get_dict()
        if 'FrameworkName' in parameters['GeneralSettings']:
            raise InputValidationError('You should not provide "FrameworkName"'
                                       ' as an input parameter. It will be generated automatically'
                                       ' by AiiDA')

        # handle input structure
        if 'structure' in self.inputs:
            self.inputs.structure.export(folder.get_abs_path(self.COORDS_FILE), fileformat='cif')
            parameters['GeneralSettings']['Framework'] = '0'
            parameters['GeneralSettings']['FrameworkName'] = 'framework'

        # handle restart
        if 'restart_folder' in self.inputs:
            self._create_restart(folder)

        # Get settings
        if 'setting' in self.inputs:
            settings = self.inputs.settings.get_dict()
        else:
            settings = {}

        # handle block pockets
        # This part needs to be reformulated.
        # for i, block_pocket in enumerate('block_pockets'):
        #     if block_pocket:
        #         parameters_dict['Component'][i][
        #             'BlockPocketsFileName'] = 'component_{}'.format(i)
        #         parameters_dict['Component'][i]['BlockPockets'] = 'yes'
        #         copyfile(
        #             block_pocket.get_file_abs_path(),
        #             folder.get_subfolder(".").get_abs_path(
        #                 'component_{}.block'.format(i)))

        # block_pockets = []
        # for i in range(n_components):
        #     bp = inputdict.pop('block_component_{}'.format(i), None)
        #     if bp:
        #         if isinstance(bp, SinglefileData):
        #             block_pockets.append(bp)
        #         else:
        #             raise InputValidationError(
        #                 "Block pockets should be either None, or of the type SinglefileData."
        #                 "You provided the object {} of type {}".format(
        #                     bp, type(bp)))
        #     else:
        #         block_pockets.append(None)

        # write raspa input file
        inp = RaspaInput(parameters)
        with open(folder.get_abs_path(self.INPUT_FILE), "w") as fobj:
            fobj.write(inp.render())

        # create code info
        codeinfo = CodeInfo()
        codeinfo.cmdline_params = settings.pop('cmdline', []) + [self.INPUT_FILE]
        codeinfo.code_uuid = self.inputs.code.uuid

        # create calc info
        calcinfo = CalcInfo()
        calcinfo.stdin_name = self.INPUT_FILE
        calcinfo.uuid = self.uuid
        calcinfo.cmdline_params = codeinfo.cmdline_params
        calcinfo.stdin_name = self.INPUT_FILE
        #calcinfo.stdout_name = self.OUTPUT_FILE
        calcinfo.codes_info = [codeinfo]

        # file lists
        calcinfo.remote_symlink_list = []
        if 'file' in self.inputs:
            calcinfo.local_copy_list = []
            for fobj in self.inputs.file.values():
                calcinfo.local_copy_list.append((fobj.uuid, fobj.filename, fobj.filename))

        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [[self.OUTPUT_FILE, '.', 0], [self.RESTART_FILE, '.', 0]]
        calcinfo.retrieve_list += settings.pop('additional_retrieve_list', [])

        # check for left over settings
        if settings:
            raise InputValidationError("The following keys have been found " +
                                       "in the settings input node {}, ".format(self.pk) + "but were not understood: " +
                                       ",".join(list(settings.keys())))

        return calcinfo

    # --------------------------------------------------------------------------
    def _create_restart(self, folder):
        """Extract restart information from the previous RASPA calculation"""
        restart_folder = self.inputs.restart_folder
        if not isinstance(restart_folder, FolderData):
            raise InputValidationError("retrieved parent folder is of type {}, "
                                       "but not FolderData".format(type(restart_folder)))

        for fname in restart_folder.get_folder_list():
            if "restart" in fname:
                content = restart_folder.get_file_content(fname)
                break
        else:
            raise InputValidationError("Restart was requested but the restart "
                                       "file was not found in the previos calculation.")

        genset = self.inputs.parameters.get_dict()['GeneralSettings']
        (n_x, n_y, n_z) = tuple(map(int, genset['UnitCells'].split()))
        restart_fname = "restart_%s_%d.%d.%d_%lf_%lg" % ("framework", n_x, n_y, n_z, genset['ExternalTemperature'],
                                                         genset['ExternalPressure'])

        restart_fname = folder.get_subfolder('RestartInitial/System_0', create=True).get_abs_path(restart_fname)
        with open(restart_fname, "w") as fobj:
            fobj.write(content)

        self.input['GeneralSettings']['RestartFile'] = True


# ==============================================================================
class RaspaInput:
    """Convert input dictionary into input file"""

    def __init__(self, params):
        self.params = params

    # --------------------------------------------------------------------------
    def render(self):
        """Perform conversion"""
        output = ["!!! Generated by AiiDA !!!"]
        section = self.params.pop("GeneralSettings")
        self._render_section(output, section)

        section = self.params.pop("Component")
        for i, molec in enumerate(section):
            output.append('Component %d MoleculeName %s' % (i, molec.pop("MoleculeName")))
            self._render_section(output, molec, indent=3)
        return "\n".join(output)

    # --------------------------------------------------------------------------
    @staticmethod
    def _render_section(output, params, indent=0):
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
                output.append('{}{} {}'.format(' ' * indent, key, ' '.join(str(p) for p in val)))
            elif isinstance(val, bool):
                val_str = 'yes' if val else 'no'
                output.append('{}{} {}'.format(' ' * indent, key, val_str))
            else:
                output.append('{}{} {}'.format(' ' * indent, key, val))
