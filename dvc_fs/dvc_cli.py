"""
Interface to execute DVC commands.

@Piotr Styczyński 2021
"""
import io
import os
import subprocess
import sys
import threading
import configparser
from io import StringIO

import semantic_version

from dvc_fs.config import get_config
from dvc_fs.exceptions import (DVCCliCommandError, DVCInvalidVersion,
                               DVCMissingExecutableError)
from dvc_fs.logs import LOGS

try:
    from dvc import __version__ as _call_dvc_main_version
    from dvc.main import main as call_dvc_main

    call_dvc_main_version = semantic_version.Version(_call_dvc_main_version)
except ModuleNotFoundError:
    call_dvc_main = None
    call_dvc_main_version = None

from typing import Callable, List, Optional, Dict


def get_sys_exit_noop(
        original_callback: Callable[[int], None]
) -> Callable[[int], None]:
    """
    Create fake handler for system exit to prevent command line from killing Python
    process by a mistake.

    :param original_callback: original sys.exit handler
    :returns: Dummy sys.exit handler
    """

    def sys_exit_noop(dumb_code=0):
        nonlocal original_callback
        if dumb_code != 0:
            LOGS.dvc.error(
                "Invalid exit code was returned by the DVC. The program will be terminated."
            )
            original_callback(dumb_code)
        return None

    return sys_exit_noop


class DVCLocalCli:
    """
    DVC low-level command interface.
    """

    working_path: str

    def __init__(self, path: str):
        """
        Create DVC interface for a given working directory.
        The working directory should be existing, configured DVC repo.

        :param path: Path to existing, local, cloned DVC repo
        """
        self.working_path = path

    @staticmethod
    def _check_dvc_shell_executable() -> semantic_version.Version:
        """
        Check if DVC executable is accessible from the shell.
        Raises dvc_fs.exceptions.DVCMissingExecutableError if the executable is not found.
        """
        cmd = " ".join(["dvc", "version"])
        p = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE
        )
        out, err = p.communicate()
        if p.returncode != 0:
            raise DVCMissingExecutableError()
        try:
            text = (
                out.decode()
                    .split("\n")[0]
                    .replace("DVC version: ", "")
                    .split("(")[0]
                    .replace(" ", "")
            )
            ver = semantic_version.Version(text)
            if not get_config().dvc_version_constraint.match(ver):
                raise DVCInvalidVersion(
                    "DVC executable in your PATH has invalid version",
                    ver,
                    get_config().dvc_version_constraint,
                )
            return ver
        except ValueError:
            raise DVCMissingExecutableError()

    def _execute_call(
            self,
            args: List[str],
            path: Optional[str] = None,
            collect_output: bool = True,
            input: Optional[str] = None,
            use_shell: bool = True,
            spawn_process: bool = False,
    ) -> str:
        """
        Helper method to execute dvc command.
        :param args: Command arguments
        :param path: Override working path for the command
        :param collect_output: Should return output as a string?
        :param input: Optional stdin input as string
        :param use_shell: Use shell dvc command rather than DVC Python package
        :param spawn_process: Spawn new process to invoke the command (useful when sys.exit is glitched)
        :returns: Output of the command as string (stdout) or empty string if collect_output is False
        """

        if path is None:
            path = self.working_path

        if call_dvc_main is None:
            use_shell = True
        else:
            if not get_config().dvc_version_constraint.match(
                    call_dvc_main_version
            ):
                # DVC package has invalid version
                use_shell = True

        if use_shell:
            cmd = " ".join(["dvc", *args])
            LOGS.dvc.debug(f"Spawn process (DVC): {cmd} (cwd={path})")
            DVCLocalCli._check_dvc_shell_executable()
            p = subprocess.Popen(
                cmd,
                shell=True,
                cwd=path,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
            )
            out, err = p.communicate()
            if p.returncode != 0:
                raise DVCCliCommandError(cmd, out.decode(), p.returncode, path)
            return ""
        elif spawn_process:
            LOGS.dvc.debug("Spawn process (DVC)")
            t = threading.Thread(
                target=self._execute_call,
                args=(args,),
                kwargs=dict(
                    path=path,
                    collect_output=collect_output,
                    input=input,
                    spawn_process=False,
                ),
            )
            t.start()
            t.join()
            LOGS.dvc.debug("Process finished (DVC)")
            return ""

        cwd = os.getcwd()
        os.chdir(path)
        call_args = args
        sys.argv = call_args
        LOGS.dvc.debug(
            "Running DVC command: {} (path: {})".format(
                " ".join(sys.argv), path
            )
        )

        stdout = sys.stdout
        stdin = sys.stdin
        fake_stdout = None
        sysexit = sys.exit

        if collect_output:
            fake_stdout = io.StringIO("")
            sys.stdout = fake_stdout

        if input is not None:
            stream = StringIO()
            stream.write(input)
            stream.seek(0)
            sys.stdin = stream

        sys.exit = get_sys_exit_noop(sysexit)

        res = call_dvc_main(call_args)
        sys.stdout = stdout
        sys.stdin = stdin
        sys.exit = sysexit
        os.chdir(cwd)

        if collect_output:
            res = fake_stdout.getvalue()

        return res

    def dvc_set_storage_config_option(
            self,
            remote_name: str,
            key: str,
            value: str,
    ) -> Optional[str]:
        config = configparser.ConfigParser()
        config_path = os.path.join(self.working_path, ".dvc", "config")
        config.read(config_path)
        old_key_value: Optional[str] = None
        for config_key in config:
            if config_key.startswith("'remote "):
                current_remote_name = config_key.replace("'remote ", "")[1:-2]
                storage_conf = config[config_key]
                if current_remote_name == remote_name:
                     if key in storage_conf:
                         old_key_value = storage_conf[key]
                     storage_conf[key] = value
                config[config_key] = storage_conf
        with open(config_path, "w") as configfile:
            config.write(configfile)
        return old_key_value

    def init_dvc(self,
                 storage_url: Optional[str] = None,
                 additional_storage_settings: Optional[Dict[str, str]] = None,
                 ):
        if not os.path.isdir(os.path.join(self.working_path, ".dvc")):
            LOGS.dvc.debug(
                f"Initializing DVC repo (path {self.working_path}). "
                f"Storage is {'' if storage_url is not None else 'not '}configured"
            )
            self._execute_call(["init"])
            if storage_url is not None:
                LOGS.dvc.debug("Initializing DVC repo storage")
                self._execute_call(
                    ["remote", "add", "-d", "storage", f"'{storage_url}'"]
                )
            if additional_storage_settings and storage_url:
                for key in additional_storage_settings:
                    LOGS.dvc.debug(f"Configure storage option {key} for the repository")
                    self.dvc_set_storage_config_option("storage", key, additional_storage_settings[key])
        else:
            LOGS.dvc.debug(
                f"DVC repo won't be initialized because .dvc folder already exists! (path {self.working_path})"
            )
    
    def cleanup_remote(self):
        self._execute_call(["gc", "--workspace", "--cloud", "--all-branches"])
        
    def remove(self, path: str):
        """
        Add given path to DVC
        :param path: Path to the DVC file
          (note this is path to the DVC metafile so the path should end with .dvc extension)
        """
        self._execute_call(["remove", f"'{path}.dvc'"])


    def add(self, path: str):
        """
        Add given path to DVC
        :param path: Path to the DVC file
          (note this is path to the DVC metafile so the path should end with .dvc extension)
        """
        self._execute_call(["add", f"'{path}'"])

    def pull_path(self, file_path: str):
        """
        Pull DVC repo
        """
        self._execute_call(["pull", f"'{file_path}'"])

    def push(self):
        """
        Push DVC changes upstream.
        """
        self._execute_call(["push"])
