"""Raspa input plugin."""
import os
from pathlib import Path
from shutil import copyfile, copytree

from aiida.common import CalcInfo, CodeInfo, InputValidationError

# from aiida.cmdline.utils import echo
from aiida.engine import CalcJob
from aiida.orm import Dict, FolderData, List, RemoteData, SinglefileData
from aiida.plugins import DataFactory

from aiida_raspa.utils import RaspaInput

# data objects
CifData = DataFactory("core.cif")  # pylint: disable=invalid-name


class RaspaCalculation(CalcJob):
    """This is a RaspaCalculation, subclass of CalcJob, to prepare input for RASPA code.
    For information on RASPA, refer to: https://github.com/iraspa/raspa2.
    """

    # Defaults
    INPUT_FILE = "simulation.input"
    OUTPUT_FOLDER = "Output"
    RESTART_FOLDER = "Restart"
    PROJECT_NAME = "aiida"
    DEFAULT_PARSER = "raspa"

    @classmethod
    def define(cls, spec):
        super().define(spec)

        # Input parameters
        spec.input("parameters", valid_type=Dict, required=True, help="Input parameters")
        spec.input_namespace("framework", valid_type=CifData, required=False, dynamic=True, help="Input framework(s)")
        spec.input_namespace(
            "block_pocket", valid_type=SinglefileData, required=False, dynamic=True, help="Zeo++ block pocket file"
        )
        spec.input_namespace(
            "file", valid_type=SinglefileData, required=False, dynamic=True, help="Additional input file(s)"
        )
        spec.input("settings", valid_type=Dict, required=False, help="Additional input parameters")
        spec.input(
            "parent_folder",
            valid_type=RemoteData,
            required=False,
            help="Remote folder used to continue the same simulation stating from the binary restarts.",
        )
        spec.input(
            "retrieved_parent_folder",
            valid_type=FolderData,
            required=False,
            help="To use an old calculation as a starting poing for a new one.",
            validator=cls.validate_retrieved_parent_folder,
        )
        spec.inputs["metadata"]["options"]["parser_name"].default = cls.DEFAULT_PARSER
        spec.inputs["metadata"]["options"]["resources"].default = {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
            "num_cores_per_mpiproc": 1,
        }
        spec.inputs["metadata"]["options"]["withmpi"].default = False

        # Output parameters
        spec.output("output_parameters", valid_type=Dict, required=True, help="The results of a calculation")
        spec.output("warnings", valid_type=List, required=False, help="Warnings that appeared during the calculation")

        # Exit codes
        spec.exit_code(
            100, "ERROR_NO_RETRIEVED_FOLDER", message="The retrieved folder data node could not be accessed."
        )
        spec.exit_code(101, "ERROR_NO_OUTPUT_FILE", message="The retrieved folder does not contain an output file.")
        spec.exit_code(
            102, "ERROR_SIMULATION_DID_NOT_START", message='The output does not contain "Starting simulation".'
        )
        spec.exit_code(500, "TIMEOUT", message="The calculation could not be completed due to the lack of time.")

        # Default output node
        spec.default_output_node = "output_parameters"

    @staticmethod
    def validate_retrieved_parent_folder(value, _):
        """Validate the `retrieved_parent_folder` input."""

        repository = value.base.repository

        if "Restart" not in repository.list_object_names():
            return "Restart was requested but the restart folder was not found in the previous calculation."
        for system_path in repository.list_object_names("Restart"):
            if len(repository.list_object_names(Path("Restart") / system_path)) != 1:
                return "There was more than one file in a system directory of the `Restart` directory."

    # --------------------------------------------------------------------------
    # pylint: disable = too-many-locals
    def prepare_for_submission(self, folder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param folder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        """
        # create calc info
        calcinfo = CalcInfo()
        calcinfo.remote_copy_list = []
        calcinfo.local_copy_list = []

        # initialize input parameters
        inp = RaspaInput(self.inputs.parameters.get_dict())

        # keep order of systems in the extras
        self.node.set_extra("system_order", inp.system_order)

        # handle framework(s) and/or box(es)
        if "System" in inp.params:
            self._handle_system_section(inp.params["System"], folder)

        # handle restart
        if "retrieved_parent_folder" in self.inputs:
            calcinfo.local_copy_list.extend(self._handle_retrieved_parent_folder(inp))
            inp.params["GeneralSettings"]["RestartFile"] = True

        # handle binary restart
        if "parent_folder" in self.inputs:
            inp.params["GeneralSettings"]["ContinueAfterCrash"] = True
            calcinfo.remote_copy_list.append(
                (
                    self.inputs.parent_folder.computer.uuid,
                    os.path.join(self.inputs.parent_folder.get_remote_path(), "CrashRestart"),
                    "CrashRestart",
                )
            )

        # get settings
        if "settings" in self.inputs:
            settings = self.inputs.settings.get_dict()
        else:
            settings = {}

        # write raspa input file
        with open(folder.get_abs_path(self.INPUT_FILE), "w", encoding="utf-8") as fobj:
            fobj.write(inp.render())

        # create code info
        codeinfo = CodeInfo()
        codeinfo.cmdline_params = settings.pop("cmdline", []) + [self.INPUT_FILE]
        codeinfo.code_uuid = self.inputs.code.uuid

        calcinfo.stdin_name = self.INPUT_FILE
        calcinfo.uuid = self.uuid
        calcinfo.cmdline_params = codeinfo.cmdline_params
        calcinfo.stdin_name = self.INPUT_FILE
        # calcinfo.stdout_name = self.OUTPUT_FILE
        calcinfo.codes_info = [codeinfo]

        # file lists
        if "file" in self.inputs:
            for fobj in self.inputs.file.values():
                calcinfo.local_copy_list.append((fobj.uuid, fobj.filename, fobj.filename))

        # block pockets
        if "block_pocket" in self.inputs:
            for name, fobj in self.inputs.block_pocket.items():
                calcinfo.local_copy_list.append((fobj.uuid, fobj.filename, name + ".block"))

        calcinfo.retrieve_list = [self.OUTPUT_FOLDER, self.RESTART_FOLDER]
        calcinfo.retrieve_list += settings.pop("additional_retrieve_list", [])

        # check for left over settings
        if settings:
            raise InputValidationError(
                "The following keys have been found "
                + f"in the settings input node {self.pk}, "
                + "but were not understood: "
                + ",".join(list(settings.keys()))
            )

        return calcinfo

    def _handle_system_section(self, system_dict, folder):
        """Handle framework(s) and/or box(es)."""
        for name, sparams in system_dict.items():
            if sparams["type"] == "Framework":
                try:
                    self.inputs.framework[name].export(folder.get_abs_path(name + ".cif"), fileformat="cif")
                except KeyError as err:
                    raise InputValidationError(
                        f"You specified '{name}' framework in the input dictionary, but did not provide the input "
                        "framework with the same name"
                    ) from err

    def _handle_retrieved_parent_folder(self, inp):
        """Construct the local copy list from a the `retrieved_parent_folder` input."""
        local_copy_list = []

        parent_folder = self.inputs.retrieved_parent_folder
        base_src_path = Path("Restart")
        base_dest_path = Path("RestartInitial")

        for i_system, system_name in enumerate(inp.system_order):
            system = inp.params["System"][system_name]
            system_dir = f"System_{i_system}"

            old_fname = parent_folder.base.repository.list_object_names(base_src_path / system_dir).pop()

            if system["type"] == "Box":
                system_or_box = "Box"
                (n_x, n_y, n_z) = (1, 1, 1)
                if "ExternalPressure" not in system:
                    system["ExternalPressure"] = 0
            elif system["type"] == "Framework":
                system_or_box = system_name
                try:
                    (n_x, n_y, n_z) = tuple(map(int, system["UnitCells"].split()))
                except KeyError:
                    (n_x, n_y, n_z) = 1, 1, 1

            external_pressure = system["ExternalPressure"] if "ExternalPressure" in system else 0

            new_fname = (
                f"restart_{system_or_box:s}_{n_x:}.{n_y:d}.{n_z:d}_{system['ExternalTemperature']:f}"
                f"_{external_pressure:g}"
            )

            local_copy_list.append(
                (
                    parent_folder.uuid,
                    Path(base_src_path, system_dir, old_fname).as_posix(),
                    Path(base_dest_path, system_dir, new_fname).as_posix(),
                )
            )

        return local_copy_list
