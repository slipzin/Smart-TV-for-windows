import json
import unittest
from unittest.mock import patch

from installer.smarttv_installer import inspect_system


LSBLK = {
    "blockdevices": [{
        "name": "nvme0n1", "path": "/dev/nvme0n1", "type": "disk",
        "size": 512000000000, "model": "Test SSD", "tran": "nvme", "pttype": "gpt",
        "children": [
            {"name": "nvme0n1p1", "path": "/dev/nvme0n1p1", "type": "part",
             "size": 300000000, "fstype": "vfat", "parttype": "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"},
            {"name": "nvme0n1p3", "path": "/dev/nvme0n1p3", "type": "part",
             "size": 400000000000, "fstype": "ntfs", "label": "Windows",
             "parttype": "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7"}
        ]
    }]
}


class InstallerPreflightTests(unittest.TestCase):
    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=True)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_detects_uefi_disk_and_efi_without_enabling_install(self, run, exists, which):
        run.side_effect = [
            type("Result", (), {"stdout": json.dumps(LSBLK), "stderr": "", "returncode": 0})(),
            type("Result", (), {"stdout": "/dev/nvme0n1p3:Windows 11:Windows:chain\n", "stderr": "", "returncode": 0})(),
        ]
        report = inspect_system()
        self.assertTrue(report["uefi"])
        self.assertEqual(len(report["disks"]), 1)
        self.assertEqual(report["efi_partitions"][0]["path"], "/dev/nvme0n1p1")
        self.assertEqual(report["efi_partitions"][0]["disk_path"], "/dev/nvme0n1")
        self.assertTrue(report["windows_detected"])
        self.assertTrue(report["windows_candidates"])
        self.assertEqual(report["windows_disk_paths"], ["/dev/nvme0n1"])
        self.assertEqual(report["windows_installations"][0]["disk_path"], "/dev/nvme0n1")
        self.assertFalse(report["installation_allowed"])
        self.assertEqual(report["mode"], "read-only")

    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=False)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_non_uefi_is_warning_and_install_stays_blocked(self, run, exists, which):
        run.return_value = type("Result", (), {"stdout": json.dumps(LSBLK), "stderr": "", "returncode": 0})()
        report = inspect_system()
        self.assertFalse(report["uefi"])
        self.assertFalse(report["installation_allowed"])
        self.assertTrue(any("UEFI" in item for item in report["warnings"]))

    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=True)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_unmatched_os_prober_path_is_not_accepted_as_windows(self, run, exists, which):
        run.side_effect = [
            type("Result", (), {"stdout": json.dumps(LSBLK), "stderr": "", "returncode": 0})(),
            type("Result", (), {"stdout": "/dev/sdb3:Windows 11:Windows:chain\n", "stderr": "", "returncode": 0})(),
        ]
        report = inspect_system()
        self.assertFalse(report["windows_detected"])
        self.assertFalse(report["windows_installations"])
        self.assertTrue(report["windows_unmapped_entries"])
        self.assertTrue(any("não puderam ser associadas" in item for item in report["warnings"]))

    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=True)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_failed_os_prober_does_not_confirm_windows_from_partial_stdout(self, run, exists, which):
        run.side_effect = [
            type("Result", (), {"stdout": json.dumps(LSBLK), "stderr": "", "returncode": 0})(),
            type("Result", (), {"stdout": "/dev/nvme0n1p3:Windows 11:Windows:chain\n", "stderr": "probe failed", "returncode": 1})(),
        ]
        report = inspect_system()
        self.assertFalse(report["windows_detected"])
        self.assertFalse(report["windows_installations"])


    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=True)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_ntfs_recovery_partition_is_not_accepted_as_windows_volume(self, run, exists, which):
        recovery = json.loads(json.dumps(LSBLK))
        recovery["blockdevices"][0]["children"][1]["parttype"] = "de94bba4-06d1-4d40-a16a-bfd50179d6ac"
        run.side_effect = [
            type("Result", (), {"stdout": json.dumps(recovery), "stderr": "", "returncode": 0})(),
            type("Result", (), {"stdout": "/dev/nvme0n1p3:Windows Boot Manager:Windows:chain\n", "stderr": "", "returncode": 0})(),
        ]
        report = inspect_system()
        self.assertFalse(report["windows_detected"])
        self.assertFalse(report["windows_installations"])
        self.assertFalse(report["windows_volume_candidates"])
if __name__ == "__main__":
    unittest.main()