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

    def test_moonlight_and_steam_link_are_streaming_clients(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            moonlight = self.write(root, "moonlight.desktop",
                "[Desktop Entry]\nType=Application\nName=Moonlight\n"
                "Exec=/usr/bin/true\nCategories=Game;Network;\n")
            steam_link = self.write(root, "steam-link.desktop",
                "[Desktop Entry]\nType=Application\nName=Steam Link\n"
                "Exec=/usr/bin/true\nCategories=Game;\n")
            with mock.patch("smarttv.shutil.which", return_value="/usr/bin/true"):
                moon_app = smarttv.parse_desktop_file(moonlight)
                link_app = smarttv.parse_desktop_file(steam_link)
            self.assertTrue(moon_app["is_streaming_client"])
            self.assertTrue(link_app["is_streaming_client"])
            self.assertTrue(moon_app["is_game"])
            self.assertFalse(moon_app["is_native_game"])

    def test_cloud_game_services_are_classified_separately_from_remote_pc_clients(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            xbox = self.write(root, "xbox.desktop",
                "[Desktop Entry]\nType=Application\nName=Xbox Cloud Gaming\n"
                "Exec=/usr/bin/true\nCategories=Game;Network;\n")
            geforce = self.write(root, "geforce.desktop",
                "[Desktop Entry]\nType=Application\nName=GeForce NOW - Steam Cloud Play\n"
                "Exec=/usr/bin/true\nCategories=Game;Network;\n")
            moonlight = self.write(root, "moonlight.desktop",
                "[Desktop Entry]\nType=Application\nName=Moonlight\n"
                "Exec=/usr/bin/true\nCategories=Game;Network;\n")
            with mock.patch("smarttv.shutil.which", return_value="/usr/bin/true"):
                xbox_app = smarttv.parse_desktop_file(xbox)
                geforce_app = smarttv.parse_desktop_file(geforce)
                moonlight_app = smarttv.parse_desktop_file(moonlight)
            self.assertTrue(xbox_app["is_game"])
            self.assertTrue(xbox_app["is_cloud_game"])
            self.assertTrue(geforce_app["is_cloud_game"])
            self.assertFalse(moonlight_app["is_cloud_game"])
            self.assertTrue(moonlight_app["is_streaming_client"])

    def test_game_category_and_known_launchers_are_marked(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            native = self.write(root, "native.desktop",
                "[Desktop Entry]\nType=Application\nName=SuperTuxKart\n"
                "Exec=/usr/bin/true\nCategories=Game;ArcadeGame;\n")
            heroic = self.write(root, "heroic.desktop",
                "[Desktop Entry]\nType=Application\nName=Heroic Games Launcher\n"
                "Exec=/usr/bin/true\nCategories=Utility;\n")
            with mock.patch("smarttv.shutil.which", return_value="/usr/bin/true"):
                native_app = smarttv.parse_desktop_file(native)
                heroic_app = smarttv.parse_desktop_file(heroic)
            self.assertTrue(native_app["is_game"])
            self.assertTrue(native_app["is_native_game"])
            self.assertTrue(heroic_app["is_game"])
            self.assertFalse(heroic_app["is_native_game"])

    def test_steam_library_manifests_become_game_entries(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            steamapps = home / ".steam/steam/steamapps"
            steamapps.mkdir(parents=True)
            (steamapps / "appmanifest_1234.acf").write_text(
                '"AppState"\n{\n  "appid" "1234"\n  "name" "Example Game"\n}\n',
                encoding="utf-8")
            games = smarttv.steam_games(home)
            self.assertEqual(len(games), 1)
            self.assertEqual(games[0]["id"], "steam-game:1234")
            self.assertEqual(games[0]["title"], "Example Game")
            self.assertEqual(games[0]["argv"], ["steam", "-bigpicture", "-applaunch", "1234"])

    def test_gaming_preferences_are_private_and_persistent(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            self.assertTrue(smarttv.set_gaming_setting("mangohud", True, home))
            path = home / ".config/smart-tv/gaming.json"
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertTrue(smarttv.gaming_settings(home)["mangohud"])
            self.assertFalse(smarttv.set_gaming_setting("unknown", True, home))

    def test_experience_profile_is_persistent_and_validated(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            self.assertEqual(smarttv.gaming_settings(home)["profile"], "tv")
            self.assertTrue(smarttv.set_experience_profile("console", home))
            self.assertEqual(smarttv.gaming_settings(home)["profile"], "console")
            self.assertFalse(smarttv.set_experience_profile("unknown", home))

    def test_native_games_get_optional_performance_wrappers(self):
        item = {"id": "native", "is_native_game": True, "argv": ["/usr/games/example"]}
        which = { "gamemoderun": "/usr/bin/gamemoderun", "mangohud": "/usr/bin/mangohud" }
        with mock.patch("smarttv.gaming_settings", return_value={"gamemode": True, "mangohud": True}), \
             mock.patch("smarttv.shutil.which", side_effect=lambda name: which.get(name)), \
             mock.patch("smarttv.subprocess.Popen") as process:
            self.assertTrue(smarttv.launch_app([item], "native"))
        argv = process.call_args.args[0]
        env = process.call_args.kwargs["env"]
        self.assertEqual(argv, ["/usr/bin/gamemoderun", "/usr/games/example"])
        self.assertEqual(env["MANGOHUD"], "1")
        self.assertEqual(env["MANGOHUD_DLSYM"], "1")

    def test_launcher_is_not_wrapped_as_a_game_process(self):
        item = {"id": "steam", "is_native_game": False, "is_game": True, "argv": ["/usr/bin/steam"]}
        with mock.patch("smarttv.shutil.which", side_effect=AssertionError("should not probe overlays")), \
             mock.patch("smarttv.subprocess.Popen") as process:
            self.assertTrue(smarttv.launch_app([item], "steam"))
        self.assertEqual(process.call_args.args[0], ["/usr/bin/steam"])

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

    def test_app_catalogue_exposes_game_flag(self):
        self.server.apps = [{"id": "native", "title": "Example Game", "icon": "", "color": "#000",
                             "is_game": True, "argv": ["/usr/bin/true"]}]
        with mock.patch("smarttv.discover_apps", return_value=self.server.apps):
            status, _, body = self.get("/api/apps")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body.decode("utf-8"))["apps"][0]["is_game"])

    def test_app_catalogue_returns_cloud_game_metadata(self):
        self.server.apps = [{"id": "xboxcloud", "title": "Xbox Cloud Gaming",
                             "icon": "", "color": "#000", "is_game": True,
                             "is_cloud_game": True, "is_streaming_client": False}]
        with mock.patch("smarttv.discover_apps", return_value=self.server.apps):
            status, _, body = self.get("/api/apps")
        self.assertEqual(status, 200)
        app = json.loads(body.decode("utf-8"))["apps"][0]
        self.assertTrue(app["is_cloud_game"])
        self.assertFalse(app["is_streaming_client"])

    def test_gaming_api_updates_valid_preferences(self):
        with mock.patch.dict("os.environ", {"XDG_CONFIG_HOME": self.temp.name}):
            status, _, body = self.get("/api/gaming?key=gamemode&enabled=0")
            self.assertEqual(status, 200)
            result = json.loads(body.decode("utf-8"))
            self.assertFalse(result["gamemode"])
            self.assertTrue((Path(self.temp.name) / "smart-tv/gaming.json").is_file())

    def test_profile_api_reads_and_updates_mode(self):
        with mock.patch.dict("os.environ", {"XDG_CONFIG_HOME": self.temp.name}):
            status, _, body = self.get("/api/profile")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body.decode("utf-8"))["profile"], "tv")
            status, _, body = self.get("/api/profile?mode=console")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body.decode("utf-8"))["profile"], "console")
            self.assertTrue((Path(self.temp.name) / "smart-tv/gaming.json").is_file())

    def test_profile_api_rejects_unknown_mode(self):
        status, _, body = self.get("/api/profile?mode=server")
        self.assertEqual(status, 400)
        self.assertFalse(json.loads(body.decode("utf-8"))["ok"])

    def test_gaming_api_rejects_unknown_settings(self):
        status, _, body = self.get("/api/gaming?key=unknown&enabled=1")
        self.assertEqual(status, 400)
        self.assertFalse(json.loads(body.decode("utf-8"))["ok"])

    def test_app_catalogue_api_returns_json(self):
        status, headers, body = self.get("/api/apps")
        self.assertEqual(status, 200)
        self.assertIn("application/json", headers.get("Content-Type", ""))
        self.assertIn("apps", json.loads(body.decode("utf-8")))


if __name__ == "__main__":
    unittest.main()
