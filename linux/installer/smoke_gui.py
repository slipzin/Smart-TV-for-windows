"""Offscreen smoke test for the actual PyQt installer wizard.

Run inside the built Debian root filesystem:
QT_QPA_PLATFORM=offscreen PYTHONPATH=/usr/local/lib/smarttv python3 -m installer.smoke_gui
"""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

import installer.gui as gui
from installer.disk_plan import EFI_GUID, GIB


def main() -> int:
    region = {
        "disk_path": "/dev/nvme0n1",
        "start_bytes": 512 * 1024 * 1024,
        "end_bytes": 512 * 1024 * 1024 + 100 * GIB - 1,
        "size_bytes": 100 * GIB,
    }
    inventory = {
        "uefi": True,
        "windows_detected": ["/dev/nvme0n1p3:Windows 11:Windows:chain"],
        "windows_candidates": [],
        "windows_disk_paths": ["/dev/nvme0n1"],
        "windows_installations": [{
            "entry": "/dev/nvme0n1p3:Windows 11:Windows:chain",
            "boot_partition_path": "/dev/nvme0n1p3",
            "disk_path": "/dev/nvme0n1",
        }],
        "bitlocker_detected": False,
        "efi_partitions": [{
            "path": "/dev/nvme0n1p1",
            "disk_path": "/dev/nvme0n1",
            "size_bytes": 300 * 1024 * 1024,
            "fstype": "vfat",
            "parttype": EFI_GUID,
            "label": "EFI",
        }],
        "disks": [{
            "path": "/dev/nvme0n1",
            "model": "Smoke Test SSD",
            "size_bytes": 512 * GIB,
            "partition_table": "gpt",
        }],
        "warnings": [],
    }

    # Keep the smoke test deterministic and ensure it never probes real disks.
    gui.inspect_system = lambda: inventory
    gui.inspect_free_regions = lambda _disk: [region]

    app = QApplication([])
    window = gui.InstallerWindow()

    assert "SIM" in window.check_summary.text(), window.check_summary.text()
    assert not window.review_ack.isChecked()

    window.disk_combo.setCurrentIndex(0)
    assert window.region_combo.count() == 1
    assert window.efi_combo.count() == 1
    window.region_combo.setCurrentIndex(0)
    window.efi_combo.setCurrentIndex(0)
    window._prepare_review()

    # A plan cannot even be marked valid until the review checkbox is explicit.
    window.validate_plan()
    assert "revisão final" in window.validation_label.text().lower(), window.validation_label.text()

    window.review_ack.setChecked(True)
    window.validate_plan()
    assert "bitlocker" in window.validation_label.text().lower(), window.validation_label.text()

    # This is a simulated user acknowledgement only; it does not change disk state.
    window.bitlocker_ack.setChecked(True)
    window.validate_plan()
    assert "PLANO VÁLIDO" in window.validation_label.text(), window.validation_label.text()

    window.close()
    app.quit()
    print("Smart TV OS installer GUI startup/review smoke test: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
