import unittest
from unittest.mock import call, patch

from encapp_tool import app_utils

ADB_DEVICE_VALID_ID = "1234567890abcde"


class TestAppUtils(unittest.TestCase):
    @patch("encapp_tool.adb_cmds.install_apk")
    @patch("encapp_tool.adb_cmds.grant_storage_permissions")
    @patch("encapp_tool.adb_cmds.grant_camera_permission")
    @patch("encapp_tool.adb_cmds.force_stop")
    def test_install_app_shall_install_encapp_apk(
        self, mock_stop, mock_perm_camera, mock_perm_store, mock_install
    ):
        app_utils.install_app(ADB_DEVICE_VALID_ID)
        mock_install.assert_called_with(ADB_DEVICE_VALID_ID, app_utils.APK_MAIN, 0)
        mock_perm_store.assert_called_with(ADB_DEVICE_VALID_ID, 0)
        mock_perm_camera.assert_called_with(ADB_DEVICE_VALID_ID, 0)
        mock_stop.assert_called_with(ADB_DEVICE_VALID_ID, "com.facebook.encapp", 0)

    @patch("encapp_tool.adb_cmds.installed_apps")
    def test_install_ok_shall_verify_if_encapp_is_installed(self, mock_apps):
        installed_encapp = [
            "com.android.package.a",
            "com.facebook.encapp",
            "com.android.package.c",
        ]
        not_installed_encapp = ["com.android.package.a", "com.android.package.b"]
        mock_apps.side_effect = [installed_encapp, not_installed_encapp]
        self.assertTrue(app_utils.install_ok(ADB_DEVICE_VALID_ID, 1))
        self.assertFalse(app_utils.install_ok(ADB_DEVICE_VALID_ID, 1))

    @patch("encapp_tool.adb_cmds.uninstall_apk")
    def test_uninstall_app_shall_uninstall_encapp(self, mock_uninstall):
        app_utils.uninstall_app(ADB_DEVICE_VALID_ID, 1)
        mock_uninstall.assert_called_with(
            ADB_DEVICE_VALID_ID, "com.facebook.encapp", 1
        )

    @patch("encapp_tool.adb_cmds.get_app_pid")
    def test_wait_for_exit_shall_keep_running_until_encapp_stops(
            self, mock_get_pid
    ):
        mock_get_pid.side_effect = [1234, 1234, -1]
        with patch("encapp_tool.app_utils.time.sleep") as mock_sleep:
            app_utils.wait_for_exit(ADB_DEVICE_VALID_ID, 1)
            mock_sleep.assert_has_calls([call(1), call(1)])
            mock_get_pid.assert_has_calls([
                call(ADB_DEVICE_VALID_ID, "com.facebook.encapp", 1),
                call(ADB_DEVICE_VALID_ID, "com.facebook.encapp", 1),
                call(ADB_DEVICE_VALID_ID, "com.facebook.encapp", 1)
            ], any_order=False)

    @patch("encapp_tool.adb_cmds.get_app_pid")
    def test_wait_for_exit_shall_skip_if_failure(
            self, mock_get_pid
    ):
        mock_get_pid.side_effect = [-2]
        with patch("encapp_tool.app_utils.time.sleep") as mock_sleep:
            with self.assertRaises(ValueError) as exc:
                app_utils.wait_for_exit(ADB_DEVICE_VALID_ID, 1)
                self.assertEqual(exc.exception.__str__(),
                                 "error: unable to parse encapp PID")
            mock_sleep.assert_not_called()
            mock_get_pid.assert_called_with(
                ADB_DEVICE_VALID_ID, "com.facebook.encapp", 1
            )

    @patch("encapp_tool.adb_cmds.get_app_pid")
    def test_wait_for_exit_shall_skip_if_encapp_not_running(
            self, mock_get_pid
    ):
        mock_get_pid.side_effect = [-1]
        with patch("encapp_tool.app_utils.time.sleep") as mock_sleep:
            app_utils.wait_for_exit(ADB_DEVICE_VALID_ID, 1)
            mock_sleep.assert_not_called()
            mock_get_pid.assert_called_with(
                ADB_DEVICE_VALID_ID, "com.facebook.encapp", 1
            )

    @patch("encapp_tool.adb_cmds.remove_files_using_regex")
    def test_remove_gen_files_shall_remove_encapp_gen_files(
            self, mock_rm_files
    ):
        app_utils.remove_gen_files(ADB_DEVICE_VALID_ID, 1)
        mock_rm_files.assert_called_with(
            ADB_DEVICE_VALID_ID,
            r"encapp_.*",
            "/sdcard/",
            1
        )
