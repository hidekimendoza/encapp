#!/usr/bin/env python3

import os
import time

from encapp_tool import adb_cmds
from encapp_tool._version import __version__

APPNAME_MAIN = "com.facebook.encapp"
ACTIVITY = f"{APPNAME_MAIN}/.MainActivity"

MODULE_PATH = os.path.dirname(__file__)
SCRIPT_DIR = os.path.abspath(os.path.join(MODULE_PATH, os.pardir))

RELEASE_APK_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, os.pardir, "app", "releases")
)
APK_NAME_MAIN = f"{APPNAME_MAIN}-v{__version__}-debug.apk"
APK_MAIN = os.path.join(RELEASE_APK_DIR, APK_NAME_MAIN)

ENCAPP_OUTPUT_FILE_NAME_RE = r"encapp_.*"
ENCAPP_GEN_FILES_DIR = "/sdcard/"


def install_app(serial, debug=0):
    """Install encapp apk and grant required permissions

    Args:
        serial (str): Android device serial no.
        debug (int): Debug level
    """
    adb_cmds.install_apk(serial, APK_MAIN, debug)
    adb_cmds.grant_camera_permission(serial, debug)
    adb_cmds.grant_storage_permissions(serial, debug)
    adb_cmds.force_stop(serial, APPNAME_MAIN, debug)


def install_ok(serial: str, debug=0) -> bool:
    """Verify encapp installation at android device

    Args:
        serial (str): Android device serial no.
        debug (int): Debug level

    Returns:
        True if encapp is installed at device, False otherwise.
    """
    package_list = adb_cmds.installed_apps(serial, debug)
    if APPNAME_MAIN not in package_list:
        return False
    return True


def uninstall_app(serial: str, debug=0):
    """Uninstall encapp at android device

    Args:
        serial (str): Android device serial no.
        debug (int): Debug level
    """
    adb_cmds.uninstall_apk(serial, APPNAME_MAIN, debug)


def wait_for_exit(serial: str, debug=0):
    """Wait until encapp process is not longer running at device

    Args:
        serial (str): Android device serial no.
        debug (int): Debug level
    """
    pid = -1
    current = 1
    while current != -1:
        current = adb_cmds.get_app_pid(serial, APPNAME_MAIN, debug)
        if current == -2:
            raise ValueError("error: unable to parse encapp PID")
        if current > 0:
            pid = current
            # Wait only if encapp is running
            time.sleep(1)
    if pid != -1:
        print(f'Exit from {pid}')
    else:
        print(f'{APPNAME_MAIN} was not active')


def remove_gen_files(serial: str, debug=0):
    """Remove any files that are generated in previous runs

    Args:
        serial (str): Android device serial no.
        debug (int): Debug level
    """
    adb_cmds.remove_files_using_regex(
        serial,
        ENCAPP_OUTPUT_FILE_NAME_RE,
        ENCAPP_GEN_FILES_DIR,
        debug
    )
