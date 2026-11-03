import tempfile, unittest
from pathlib import Path
from unittest import mock
import smarttv

class DesktopTests(unittest.TestCase):
    def write(self, folder, filename, body):
        path=folder/filename; path.write_text(body,encoding="utf-8"); return path
    def test_known_ids(self):
        self.assertEqual(smarttv.canonical_app("Netflix for Linux")[0],"netflix")
        self.assertEqual(smarttv.canonical_app("Steam (Runtime)")[0],"steam")
    def test_hidden_and_terminal_entries_are_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            hidden=self.write(root,"hidden.desktop","[Desktop Entry]\nType=Application\nName=Hidden\nExec=/usr/bin/true\nHidden=true\n")
            terminal=self.write(root,"terminal.desktop","[Desktop Entry]\nType=Application\nName=Terminal\nExec=/usr/bin/true\nTerminal=true\n")
            self.assertIsNone(smarttv.parse_desktop_file(hidden))
            self.assertIsNone(smarttv.parse_desktop_file(terminal))
    def test_field_codes_are_removed(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.write(Path(d),"vlc.desktop","[Desktop Entry]\nType=Application\nName=VLC media player\nExec=/usr/bin/true %U\n")
            app=smarttv.parse_desktop_file(p)
            self.assertEqual(app["id"],"vlc")
            self.assertEqual(app["argv"],["/usr/bin/true"])
    def test_missing_executable_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.write(Path(d),"missing.desktop","[Desktop Entry]\nType=Application\nName=Missing\nExec=missing-executable-smarttv\n")
            with mock.patch("smarttv.shutil.which",return_value=None):
                self.assertIsNone(smarttv.parse_desktop_file(p))
    def test_discovery_deduplicates_canonical_ids(self):
        with tempfile.TemporaryDirectory() as d:
            home=Path(d); a=home/"a"; b=home/"b"; a.mkdir(); b.mkdir()
            self.write(a,"netflix.desktop","[Desktop Entry]\nType=Application\nName=Netflix\nExec=/usr/bin/true\n")
            self.write(b,"other.desktop","[Desktop Entry]\nType=Application\nName=Netflix App\nExec=/usr/bin/true\n")
            with mock.patch("smarttv.desktop_dirs",return_value=[a,b]): apps=smarttv.discover_apps(home)
            self.assertEqual(sum(x["id"]=="netflix" for x in apps),1)

if __name__=="__main__": unittest.main()
