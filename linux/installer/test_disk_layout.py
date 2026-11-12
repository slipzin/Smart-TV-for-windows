import unittest
from unittest.mock import patch

from installer.disk_layout import inspect_free_regions, parse_parted_free_regions


DISK = "/dev/nvme0n1"
DISK_SIZE = 512110190592
HEADER = f"{DISK}:{DISK_SIZE}B:nvme:512:4096:gpt:Test SSD:;"
SAMPLE = f"""BYT;
{HEADER}
1:17408B:1048575B:1031168B:Free Space;
1:1048576B:538968063B:537919488B:fat32:EFI System Partition:boot, esp;
2:538968064B:512109142015B:511570173952B:ntfs:Basic data partition:msftdata;
2:512109142016B:512110190591B:1048576B:Free Space;
"""


class DiskLayoutTests(unittest.TestCase):
    def test_parses_only_explicit_consistent_free_space_rows(self):
        regions = parse_parted_free_regions(SAMPLE, DISK)
        self.assertEqual(len(regions), 2)
        self.assertEqual(regions[0]["start_bytes"], 17408)
        self.assertEqual(regions[0]["size_bytes"], 1031168)
        self.assertEqual(regions[1]["disk_path"], DISK)
        self.assertEqual(regions[1]["disk_size_bytes"], DISK_SIZE)

    def test_accepts_valid_disk_without_unallocated_regions(self):
        self.assertEqual(parse_parted_free_regions("BYT;\n" + HEADER, DISK), [])

    def test_rejects_non_device_path(self):
        with self.assertRaises(ValueError):
            parse_parted_free_regions(SAMPLE, "nvme0n1")

    def test_rejects_header_for_a_different_disk(self):
        with self.assertRaisesRegex(ValueError, "outro dispositivo"):
            parse_parted_free_regions(SAMPLE, "/dev/sdb")

    def test_rejects_missing_or_invalid_disk_header(self):
        with self.assertRaisesRegex(ValueError, "cabeçalho"):
            parse_parted_free_regions("BYT;\n", DISK)
        for size in ("0B", "unknown", "512110190592.5B"):
            header = HEADER.replace(f"{DISK_SIZE}B", size)
            with self.subTest(size=size), self.assertRaisesRegex(ValueError, "tamanho de disco válido"):
                parse_parted_free_regions("BYT;\n" + header, DISK)

    def test_rejects_free_space_row_before_disk_header(self):
        row = "3:1000000B:2000000B:1000001B:Free Space;"
        with self.assertRaisesRegex(ValueError, "antes de confirmar o disco"):
            parse_parted_free_regions("BYT;\n" + row + "\n" + HEADER, DISK)

    def test_rejects_fractional_or_malformed_free_space_rows(self):
        row = "3:1000000.5B:2000000B:1000000B:Free Space;"
        with self.assertRaisesRegex(ValueError, "limites de espaço livre inválidos"):
            parse_parted_free_regions("BYT;\n" + HEADER + "\n" + row, DISK)

    def test_rejects_inconsistent_free_space_size(self):
        row = "3:3000000B:3999999B:900000B:Free Space;"
        with self.assertRaisesRegex(ValueError, "não corresponde"):
            parse_parted_free_regions("BYT;\n" + HEADER + "\n" + row, DISK)

    def test_rejects_region_beyond_physical_disk_size(self):
        row = "3:512110190000B:512110190600B:601B:Free Space;"
        with self.assertRaisesRegex(ValueError, "ultrapassa"):
            parse_parted_free_regions("BYT;\n" + HEADER + "\n" + row, DISK)

    def test_rejects_overlapping_free_regions(self):
        row = "3:1000000B:2000000B:1000001B:Free Space;"
        first_free_row = SAMPLE.splitlines()[2]
        with self.assertRaisesRegex(ValueError, "sobrepostas"):
            parse_parted_free_regions("BYT;\n" + HEADER + "\n" + first_free_row + "\n" + row, DISK)

    def test_rejects_duplicate_disk_headers(self):
        with self.assertRaisesRegex(ValueError, "mais de um cabeçalho"):
            parse_parted_free_regions("BYT;\n" + HEADER + "\n" + HEADER, DISK)

    @patch("installer.disk_layout.shutil.which", return_value="/usr/sbin/parted")
    @patch("installer.disk_layout.subprocess.run")
    def test_inspection_uses_read_only_print_free_command_and_c_locale(self, run, which):
        run.return_value = type("Result", (), {"returncode": 0, "stdout": SAMPLE, "stderr": ""})()
        result = inspect_free_regions(DISK)
        self.assertEqual(len(result), 2)
        args = run.call_args.args[0]
        self.assertEqual(args[-3:], ["B", "print", "free"])
        self.assertIn("--script", args)
        self.assertNotIn("mkpart", args)
        self.assertNotIn("rm", args)
        self.assertEqual(run.call_args.kwargs["env"]["LC_ALL"], "C")
        self.assertEqual(run.call_args.kwargs["env"]["LANG"], "C")


if __name__ == "__main__":
    unittest.main()
