import unittest

from installer.disk_plan import (
    EFI_GUID, GIB, MIB, InstallPlan, UnsafeInstallPlan, validate_install_plan,
)


DISK_SIZE = 512_000_000_000
FREE_START = 500 * MIB
FREE_SIZE = 100 * GIB


class DiskPlanValidationTests(unittest.TestCase):
    def setUp(self):
        self.inventory = {
            "disks": [{
                "path": "/dev/nvme0n1",
                "partition_table": "gpt",
                "size_bytes": DISK_SIZE,
            }],
            "efi_partitions": [{
                "path": "/dev/nvme0n1p1", "disk_path": "/dev/nvme0n1",
                "fstype": "vfat", "parttype": EFI_GUID, "size_bytes": 300 * MIB,
            }],
            "free_regions": [{
                "disk_path": "/dev/nvme0n1",
                "disk_size_bytes": DISK_SIZE,
                "start_bytes": FREE_START,
                "end_bytes": FREE_START + FREE_SIZE - 1,
                "size_bytes": FREE_SIZE,
            }],
            "windows_installations": [{
                "boot_partition_path": "/dev/nvme0n1p1",
                "windows_volume_path": "/dev/nvme0n1p3",
                "disk_path": "/dev/nvme0n1",
                "preliminary_only": True,
            }],
        }
        self.plan = InstallPlan(
            disk_path="/dev/nvme0n1", table="gpt", boot_mode="uefi",
            free_region_start=FREE_START,
            free_region_bytes=FREE_SIZE, root_bytes=80 * GIB,
            efi_partition_path="/dev/nvme0n1p1",
            windows_present=True, windows_pre_detected=True,
            bitlocker_acknowledged_by_user=True, user_confirmed=True,
        )

    def test_valid_plan_is_simulation_only_and_preserves_efi(self):
        result = validate_install_plan(self.plan, self.inventory)
        self.assertTrue(result["preflight_valid"])
        self.assertEqual(result["validation_scope"], "read_only_preflight_simulation")
        self.assertFalse(result["windows_installation_verified"])
        self.assertFalse(result["bitlocker_state_verified"])
        self.assertFalse(result["installation_authorized"])
        self.assertFalse(result["writes_performed"])
        self.assertFalse(result["execution_enabled"])
        self.assertFalse(result["efi"]["format"])
        self.assertTrue(result["efi"]["reuse"])
        self.assertEqual(result["efi"]["size_bytes"], 300 * MIB)
        self.assertEqual(result["disk_size_bytes"], DISK_SIZE)
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
                InstallPlan(**{**self.plan.__dict__, "windows_pre_detected": False}),
                self.inventory,
            )
        with self.assertRaises(UnsafeInstallPlan):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "bitlocker_acknowledged_by_user": False}),
                self.inventory,
            )
        with self.assertRaises(UnsafeInstallPlan):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "bitlocker_detected": True,
                               "bitlocker_acknowledged_by_user": False}),
                self.inventory,
            )
        with self.assertRaisesRegex(UnsafeInstallPlan, "volume BitLocker"):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "bitlocker_detected": True,
                               "bitlocker_acknowledged_by_user": True}),
                self.inventory,
            )

    def test_inventory_bitlocker_cannot_be_overridden_by_plan_flags(self):
        for extra in (
            {"bitlocker_detected": True},
            {"bitlocker_partitions": ["/dev/nvme0n1p4"]},
        ):
            with self.subTest(extra=extra), self.assertRaisesRegex(UnsafeInstallPlan, "BitLocker no inventário"):
                validate_install_plan(self.plan, {**self.inventory, **extra})

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
                InstallPlan(**{**self.plan.__dict__, "free_region_start": 700 * MIB}),
                self.inventory,
            )

    def test_rejects_lsblk_parted_disk_size_mismatch(self):
        disk = dict(self.inventory["disks"][0])
        disk["size_bytes"] -= 1
        inventory = {**self.inventory, "disks": [disk]}
        with self.assertRaisesRegex(UnsafeInstallPlan, "geometria confirmada"):
            validate_install_plan(self.plan, inventory)

    def test_rejects_inconsistent_free_region_end(self):
        region = dict(self.inventory["free_regions"][0])
        region["end_bytes"] -= 1
        inventory = {**self.inventory, "free_regions": [region]}
        with self.assertRaisesRegex(UnsafeInstallPlan, "geometria confirmada"):
            validate_install_plan(self.plan, inventory)

    def test_rejects_efi_from_another_disk(self):
        other = {"efi_partitions": [{
            "path": "/dev/sdb1", "disk_path": "/dev/sdb",
            "fstype": "vfat", "parttype": EFI_GUID, "size_bytes": 300 * MIB,
        }]}
        inventory = {**self.inventory, **other}
        with self.assertRaises(UnsafeInstallPlan):
            validate_install_plan(
                InstallPlan(**{**self.plan.__dict__, "efi_partition_path": "/dev/sdb1"}),
                inventory,
            )

    def test_rejects_efi_smaller_than_100_mib_or_unknown_size(self):
        for size in (99 * MIB, None):
            efi = dict(self.inventory["efi_partitions"][0])
            efi["size_bytes"] = size
            inventory = {**self.inventory, "efi_partitions": [efi]}
            with self.subTest(size=size), self.assertRaisesRegex(UnsafeInstallPlan, "menos de 100 MiB"):
                validate_install_plan(self.plan, inventory)

    def test_rejects_target_disk_without_pre_detected_windows(self):
        other_disk = {
            "disks": [{
                "path": "/dev/sdb", "partition_table": "gpt",
                "size_bytes": DISK_SIZE,
            }],
            "efi_partitions": [{
                "path": "/dev/sdb1", "disk_path": "/dev/sdb",
                "fstype": "vfat", "parttype": EFI_GUID, "size_bytes": 300 * MIB,
            }],
            "free_regions": [{
                "disk_path": "/dev/sdb", "disk_size_bytes": DISK_SIZE,
                "start_bytes": FREE_START,
                "end_bytes": FREE_START + FREE_SIZE - 1,
                "size_bytes": FREE_SIZE,
            }],
        }
        inventory = {**self.inventory, **other_disk}
        plan = InstallPlan(**{
            **self.plan.__dict__,
            "disk_path": "/dev/sdb",
            "efi_partition_path": "/dev/sdb1",
        })
        with self.assertRaisesRegex(UnsafeInstallPlan, "pré-detecção Windows não foi associada"):
            validate_install_plan(plan, inventory)


if __name__ == "__main__":
    unittest.main()
