import unittest

from installer.disk_plan import (
    EFI_GUID, GIB, InstallPlan, UnsafeInstallPlan, validate_install_plan,
)


class DiskPlanValidationTests(unittest.TestCase):
    def setUp(self):
        self.inventory = {
            "disks": [{"path": "/dev/nvme0n1", "partition_table": "gpt"}],
            "efi_partitions": [{
                "path": "/dev/nvme0n1p1", "disk_path": "/dev/nvme0n1",
                "fstype": "vfat", "parttype": EFI_GUID,
            }],
            "free_regions": [{
                "disk_path": "/dev/nvme0n1",
                "start_bytes": 500 * 1024 * 1024,
                "size_bytes": 100 * GIB,
            }],
            "windows_installations": [{
                "boot_partition_path": "/dev/nvme0n1p1",
                "disk_path": "/dev/nvme0n1",
            }],
        }
        self.plan = InstallPlan(
            disk_path="/dev/nvme0n1", table="gpt", boot_mode="uefi",
            free_region_start=500 * 1024 * 1024,
            free_region_bytes=100 * GIB, root_bytes=80 * GIB,
            efi_partition_path="/dev/nvme0n1p1",
            windows_present=True, windows_confirmed=True,
            bitlocker_cleared_by_user=True, user_confirmed=True,
        )

    def test_valid_plan_is_simulation_only_and_preserves_efi(self):
        result = validate_install_plan(self.plan, self.inventory)
        self.assertTrue(result["valid"])
        self.assertFalse(result["execution_enabled"])
        self.assertFalse(result["efi"]["format"])
        self.assertTrue(result["efi"]["reuse"])
        self.assertFalse(result["existing_partitions_modified"])

    def test_rejects_formatting_efi(self):
        with self.assertRaises(UnsafeInstallPlan):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "format_efi": True}),
                self.inventory,
            )

    def test_rejects_unconfirmed_windows_and_bitlocker(self):
        with self.assertRaises(UnsafeInstallPlan):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "windows_confirmed": False}),
                self.inventory,
            )
        with self.assertRaises(UnsafeInstallPlan):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "bitlocker_cleared_by_user": False}),
                self.inventory,
            )
        with self.assertRaises(UnsafeInstallPlan):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "bitlocker_detected": True,
                               "bitlocker_cleared_by_user": False}),
                self.inventory,
            )

    def test_rejects_non_uefi_and_small_space(self):
        with self.assertRaises(UnsafeInstallPlan):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "boot_mode": "bios"}),
                self.inventory,
            )
        with self.assertRaises(UnsafeInstallPlan):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "free_region_bytes": 20 * GIB}),
                self.inventory,
            )

    def test_rejects_free_region_not_in_fresh_geometry(self):
        with self.assertRaises(UnsafeInstallPlan):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "free_region_start": 700 * 1024 * 1024}),
                self.inventory,
            )

    def test_rejects_efi_from_another_disk(self):
        other = {"efi_partitions": [{
            "path": "/dev/sdb1", "disk_path": "/dev/sdb",
            "fstype": "vfat", "parttype": EFI_GUID,
        }]}
        inventory = {**self.inventory, **other}
        with self.assertRaises(UnsafeInstallPlan):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "efi_partition_path": "/dev/sdb1"}),
                inventory,
            )

    def test_rejects_target_disk_without_confirmed_windows(self):
        other_disk = {
            "disks": [{"path": "/dev/sdb", "partition_table": "gpt"}],
            "efi_partitions": [{
                "path": "/dev/sdb1", "disk_path": "/dev/sdb",
                "fstype": "vfat", "parttype": EFI_GUID,
            }],
            "free_regions": [{
                "disk_path": "/dev/sdb",
                "start_bytes": 500 * 1024 * 1024,
                "size_bytes": 100 * GIB,
            }],
        }
        inventory = {**self.inventory, **other_disk}
        plan = InstallPlan(**{
            **self.plan.__dict__,
            "disk_path": "/dev/sdb",
            "efi_partition_path": "/dev/sdb1",
        })
        with self.assertRaisesRegex(UnsafeInstallPlan, "Windows confirmado não foi associado"):
            validate_install_plan(plan, inventory)


if __name__ == "__main__":
    unittest.main()