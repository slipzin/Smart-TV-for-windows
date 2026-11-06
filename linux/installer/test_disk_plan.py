import unittest

from installer.disk_plan import (
    EFI_GUID, GIB, InstallPlan, UnsafeInstallPlan, validate_install_plan,
)


class DiskPlanValidationTests(unittest.TestCase):
    def setUp(self):
        self.inventory = {
            "disks": [{"path": "/dev/nvme0n1", "partition_table": "gpt"}],
            "efi_partitions": [{
                "path": "/dev/nvme0n1p1", "fstype": "vfat",
                "parttype": EFI_GUID,
            }],
        }
        self.plan = InstallPlan(
            disk_path="/dev/nvme0n1", table="gpt", boot_mode="uefi",
            free_region_start=500 * 1024 * 1024,
            free_region_bytes=100 * GIB, root_bytes=80 * GIB,
            efi_partition_path="/dev/nvme0n1p1",
            windows_present=True, user_confirmed=True,
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

    def test_rejects_unconfirmed_plan(self):
        with self.assertRaises(UnsafeInstallPlan):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "user_confirmed": False}),
                self.inventory,
            )

    def test_rejects_bitlocker_until_user_resolves_it(self):
        with self.assertRaises(UnsafeInstallPlan):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "bitlocker_detected": True}),
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


if __name__ == "__main__":
    unittest.main()
