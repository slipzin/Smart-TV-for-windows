import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import smarttv


class DesktopTests(unittest.TestCase):
    def write(self, folder, filename, body):
        path = folder / filename
        path.write_text(body, encoding="utf-8")
        return path

    def test_known_ids(self):
        self.assertEqual(smarttv.canonical_app("Netflix for Linux")[0], "netflix")
        self.assertEqual(smarttv.canonical_app("Steam (Runtime)")[0], "steam")

    def test_hidden_and_terminal_entries_are_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            hidden = self.write(root, "hidden.desktop",
                "[Desktop Entry]\nType=Application\nName=Hidden\nExec=/usr/bin/true\nHidden=true\n")
            terminal = self.write(root, "terminal.desktop",
                "[Desktop Entry]\nType=Application\nName=Terminal\nExec=/usr/bin/true\nTerminal=true\n")
            self.assertIsNone(smarttv.parse_desktop_file(hidden))
            self.assertIsNone(smarttv.parse_desktop_file(terminal))

    def test_field_codes_are_removed(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.write(Path(d), "vlc.desktop",
                "[Desktop Entry]\nType=Application\nName=VLC media player\nExec=/usr/bin/true %U\n")
            app = smarttv.parse_desktop_file(path)
            self.assertEqual(app["id"], "vlc")
            self.assertEqual(app["argv"], ["/usr/bin/true"])

    def test_missing_executable_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.write(Path(d), "missing.desktop",
                "[Desktop Entry]\nType=Application\nName=Missing\nExec=missing-executable-smarttv\n")
            with mock.patch("smarttv.shutil.which", return_value=None):
                self.assertIsNone(smarttv.parse_desktop_file(path))

    def test_discovery_deduplicates_canonical_ids(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            first, second = home / "first", home / "second"
            first.mkdir()
            second.mkdir()
            self.write(first, "netflix.desktop",
                "[Desktop Entry]\nType=Application\nName=Netflix\nExec=/usr/bin/true\n")
            self.write(second, "other.desktop",
                "[Desktop Entry]\nType=Application\nName=Netflix App\nExec=/usr/bin/true\n")
            with mock.patch("smarttv.desktop_dirs", return_value=[first, second]):
                apps = smarttv.discover_apps(home)
            self.assertEqual(sum(app["id"] == "netflix" for app in apps), 1)


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.web = root / "web"
        self.fundos = root / "Fundos"
        self.web.mkdir()
        self.fundos.mkdir()
        (self.web / "index.html").write_text("<h1>Smart TV test</h1>", encoding="utf-8")
        (self.fundos / "video.mp4").write_bytes(b"0123456789")
        self.server = smarttv.SmartTVServer(
            ("127.0.0.1", 0), smarttv.Handler, self.web, self.fundos
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def get(self, path, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        connection.request("GET", path, headers=headers or {})
        response = connection.getresponse()
        status, response_headers, body = response.status, response.headers, response.read()
        connection.close()
        return status, response_headers, body

    def test_home_page_is_served(self):
        status, headers, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        self.assertIn(b"Smart TV test", body)

    def test_range_requests_return_video_chunks(self):
        status, headers, body = self.get("/fundos/video.mp4", {"Range": "bytes=4-7"})
        self.assertEqual(status, 206)
        self.assertEqual(headers.get("Content-Range"), "bytes 4-7/10")
        self.assertEqual(body, b"4567")

    def test_path_traversal_is_rejected(self):
        status, _, _ = self.get("/%2e%2e/etc/passwd")
        self.assertEqual(status, 404)

    def test_cross_origin_launch_requests_are_rejected(self):
        status, _, body = self.get("/api/open?id=steam", {"Origin": "https://attacker.invalid"})
        self.assertEqual(status, 403)
        self.assertIn(b"same-origin", body)

    def test_app_catalogue_api_returns_json(self):
        status, headers, body = self.get("/api/apps")
        self.assertEqual(status, 200)
        self.assertIn("application/json", headers.get("Content-Type", ""))
        self.assertIn("apps", json.loads(body.decode("utf-8")))


if __name__ == "__main__":
    unittest.main()
