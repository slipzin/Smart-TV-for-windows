import json
import unittest
from unittest.mock import patch

from installer.smarttv_installer import (
    EFI_GUID, MS_BASIC_DATA_GUID, inspect_system,
)


LSBLK = {
    "blockdevices": [{
        "name": "nvme0n1", "path": "/dev/nvme0n1", "type": "disk",
        "size": 512000000000, "model": "Test SSD", "tran": "nvme", "pttype": "gpt",
        "children": [
            {"name": "nvme0n1p1", "path": "/dev/nvme0n1p1", "type": "part",
             "size": 300000000, "fstype": "vfat", "parttype": EFI_GUID},
            {"name": "nvme0n1p3", "path": "/dev/nvme0n1p3", "type": "part",
             "size": 400000000000, "fstype": "ntfs", "label": "Windows",
             "parttype": MS_BASIC_DATA_GUID}
        ]
    }]
}


def result(stdout="", stderr="", returncode=0):
    return type("Result", (), {
        "stdout": stdout, "stderr": stderr, "returncode": returncode
    })()


class InstallerPreflightTests(unittest.TestCase):
    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=True)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_detects_preliminary_windows_evidence_without_enabling_install(self, run, exists, which):
        run.side_effect = [
            result(json.dumps(LSBLK)),
            result("/dev/nvme0n1p3:Windows 11:Windows:chain\n"),
        ]
        report = inspect_system()
        self.assertTrue(report["uefi"])
        self.assertEqual(len(report["disks"]), 1)
        self.assertEqual(report["efi_partitions"][0]["path"], "/dev/nvme0n1p1")
        self.assertEqual(report["efi_partitions"][0]["disk_path"], "/dev/nvme0n1")
        self.assertTrue(report["windows_detected"])
        self.assertTrue(report["windows_candidates"])
        self.assertEqual(report["windows_disk_paths"], ["/dev/nvme0n1"])
        evidence = report["windows_installations"][0]
        self.assertEqual(evidence["disk_path"], "/dev/nvme0n1")
        self.assertEqual(evidence["windows_volume_path"], "/dev/nvme0n1p3")
        self.assertTrue(evidence["preliminary_only"])
        self.assertFalse(report["installation_allowed"])
        self.assertEqual(report["mode"], "read-only")

    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=True)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_accepts_windows_chain_on_efi_only_with_one_ntfs_basic_data_volume(self, run, exists, which):
        run.side_effect = [
            result(json.dumps(LSBLK)),
            result("/dev/nvme0n1p1:Windows Boot Manager:Windows:chain\n"),
        ]
        report = inspect_system()
        self.assertEqual(report["windows_disk_paths"], ["/dev/nvme0n1"])
        self.assertEqual(
            report["windows_installations"][0]["windows_volume_path"],
            "/dev/nvme0n1p3",
        )

    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=True)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_accepts_uefi_windows_boot_manager_entry(self, run, exists, which):
        run.side_effect = [
            result(json.dumps(LSBLK)),
            result("/dev/nvme0n1p1:Windows Boot Manager:Windows:efi\n"),
        ]
        report = inspect_system()
        self.assertEqual(report["windows_disk_paths"], ["/dev/nvme0n1"])
        evidence = report["windows_installations"][0]
        self.assertEqual(evidence["boot_partition_path"], "/dev/nvme0n1p1")
        self.assertEqual(evidence["windows_volume_path"], "/dev/nvme0n1p3")
        self.assertIn("efi-or-chain", evidence["evidence"])

    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=True)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_multiple_ntfs_basic_data_volumes_make_windows_association_ambiguous(self, run, exists, which):
        ambiguous = json.loads(json.dumps(LSBLK))
        extra = dict(ambiguous["blockdevices"][0]["children"][1])
        extra.update({
            "name": "nvme0n1p4", "path": "/dev/nvme0n1p4",
            "size": 100000000000, "label": "Data",
        })
        ambiguous["blockdevices"][0]["children"].append(extra)
        run.side_effect = [
            result(json.dumps(ambiguous)),
            result("/dev/nvme0n1p1:Windows Boot Manager:Windows:chain\n"),
        ]
        report = inspect_system()
        self.assertFalse(report["windows_detected"])
        self.assertFalse(report["windows_installations"])
        self.assertTrue(report["windows_ambiguous_entries"])
        self.assertTrue(any("ambígua" in warning for warning in report["warnings"]))

    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=False)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_non_uefi_is_warning_and_install_stays_blocked(self, run, exists, which):
        run.return_value = result(json.dumps(LSBLK))
        report = inspect_system()
        self.assertFalse(report["uefi"])
        self.assertFalse(report["installation_allowed"])
        self.assertTrue(any("UEFI" in item for item in report["warnings"]))

    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=True)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_unmatched_os_prober_path_is_not_accepted_as_windows(self, run, exists, which):
        run.side_effect = [
            result(json.dumps(LSBLK)),
            result("/dev/sdb3:Windows 11:Windows:chain\n"),
        ]
        report = inspect_system()
        self.assertFalse(report["windows_detected"])
        self.assertFalse(report["windows_installations"])
        self.assertTrue(report["windows_unmapped_entries"])

    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=True)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_failed_os_prober_does_not_confirm_windows_from_partial_stdout(self, run, exists, which):
        run.side_effect = [
            result(json.dumps(LSBLK)),
            result("/dev/nvme0n1p3:Windows 11:Windows:chain\n", "probe failed", 1),
        ]
        report = inspect_system()
        self.assertFalse(report["windows_detected"])
        self.assertFalse(report["windows_installations"])
        self.assertFalse(report["os_prober_succeeded"])

    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=True)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_ntfs_recovery_partition_is_not_accepted_as_windows_volume(self, run, exists, which):
        recovery = json.loads(json.dumps(LSBLK))
        recovery["blockdevices"][0]["children"][1]["parttype"] = "de94bba4-06d1-4d40-a16a-bfd50179d6ac"
        run.side_effect = [
            result(json.dumps(recovery)),
            result("/dev/nvme0n1p3:Windows Boot Manager:Windows:chain\n"),
        ]
        report = inspect_system()
        self.assertFalse(report["windows_detected"])
        self.assertFalse(report["windows_installations"])
        self.assertFalse(report["windows_volume_candidates"])
        self.assertTrue(report["windows_unmapped_entries"])
        self.assertFalse(report["windows_ambiguous_entries"])

    @patch("installer.smarttv_installer.shutil.which", return_value="/usr/bin/lsblk")
    @patch("installer.smarttv_installer.Path.exists", return_value=True)
    @patch("installer.smarttv_installer.subprocess.run")
    def test_rejects_windows_text_with_unsupported_probe_method(self, run, exists, which):
        run.side_effect = [
            result(json.dumps(LSBLK)),
            result("/dev/nvme0n1p3:Windows data volume:Windows:blob\n"),
        ]
        report = inspect_system()
        self.assertFalse(report["windows_detected"])


if __name__ == "__main__":
    unittest.main()
