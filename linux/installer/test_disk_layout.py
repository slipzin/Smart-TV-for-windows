import unittest
from unittest.mock import patch

from installer.disk_layout import inspect_free_regions, parse_parted_free_regions


SAMPLE = """BYT;
/dev/nvme0n1:512110190592B:nvme:512:4096:gpt:Test SSD:;
1:17408B:1048575B:1031168B:Free Space;
1:1048576B:538968063B:537919488B:fat32:EFI System Partition:boot, esp;
2:538968064B:512109142015B:511570173952B:ntfs:Basic data partition:msftdata;
2:512109142016B:512110190591B:1048576B:Free Space;
"""


class DiskLayoutTests(unittest.TestCase):
    def test_parses_only_explicit_free_space_rows(self):
        regions = parse_parted_free_regions(SAMPLE, "/dev/nvme0n1")
        self.assertEqual(len(regions), 2)
        self.assertEqual(regions[0]["start_bytes"], 17408)
        self.assertEqual(regions[0]["size_bytes"], 1031168)
        self.assertEqual(regions[1]["disk_path"], "/dev/nvme0n1")

    def test_rejects_non_device_path(self):
        with self.assertRaises(ValueError):
            parse_parted_free_regions(SAMPLE, "nvme0n1")

    @patch("installer.disk_layout.shutil.which", return_value="/usr/sbin/parted")
    @patch("installer.disk_layout.subprocess.run")
    def test_inspection_uses_read_only_print_free_command(self, run, which):
        run.return_value = type("Result", (), {"returncode": 0, "stdout": SAMPLE, "stderr": ""})()
        result = inspect_free_regions("/dev/nvme0n1")
        self.assertEqual(len(result), 2)
        args = run.call_args.args[0]
        self.assertEqual(args[-3:], ["B", "print", "free"])
        self.assertNotIn("mkpart", args)
        self.assertNotIn("rm", args)


if __name__ == "__main__":
    unittest.main()
