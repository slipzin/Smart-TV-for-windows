import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILES = ROOT / "linux" / "profiles"
INSTALLER = ROOT / "linux" / "gaming" / "install-extras.sh"
BUILD = ROOT / "linux" / "build-iso.sh"
UI = ROOT / "web" / "home.js"
BACKEND = ROOT / "linux" / "smarttv.py"


def packages(path):
    return [
        line.split("#", 1)[0].strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.split("#", 1)[0].strip()
    ]


class ProfileManifestTests(unittest.TestCase):
    def test_tv_manifest_contains_media_network_and_controller_basics(self):
        tv = set(packages(PROFILES / "tv-packages.txt"))
        for item in (
            "plasma-desktop", "chromium", "flatpak", "plasma-discover",
            "bluez", "blueman", "steam-devices", "pipewire-audio",
            "mesa-vulkan-drivers", "kodi", "vlc",
        ):
            with self.subTest(package=item):
                self.assertIn(item, tv)

    def test_tv_manifest_excludes_local_console_stack(self):
        tv = set(packages(PROFILES / "tv-packages.txt"))
        console_only = {
            "steam-installer", "wine", "wine64", "wine32:i386", "winetricks",
            "lutris", "gamemode", "mangohud", "vulkan-tools", "gamescope",
            "dosbox", "scummvm",
        }
        flatpaks = set(packages(PROFILES / "console-flatpaks.txt"))
        self.assertTrue(console_only.isdisjoint(tv), console_only.intersection(tv))
        for item in (
            "com.heroicgameslauncher.hgl", "com.usebottles.bottles",
            "org.libretro.RetroArch", "org.DolphinEmu.dolphin-emu",
            "net.pcsx2.PCSX2", "net.rpcs3.PCSX3",
        ):
            self.assertIn(item, flatpaks)
        for item in flatpaks:
            self.assertNotIn(item, tv)

    def test_console_apt_manifest_contains_required_local_gaming_runtime(self):
        console = set(packages(PROFILES / "console-apt-packages.txt"))
        for item in (
            "steam-installer", "libglx-mesa0:i386",
            "mesa-vulkan-drivers:i386", "libgl1-mesa-dri:i386",
            "gamemode", "mangohud", "lutris", "vulkan-tools",
            "wine", "wine64", "wine32:i386", "winetricks",
            "dosbox", "scummvm",
        ):
            with self.subTest(package=item):
                self.assertIn(item, console)

    def test_build_uses_only_tv_manifest_for_the_base_iso(self):
        build = BUILD.read_text(encoding="utf-8")
        self.assertIn('"$ROOT/linux/profiles/tv-packages.txt"', build)
        self.assertIn('"$WORK/config/package-lists/smarttv.list.chroot"', build)
        self.assertIn("console-apt-packages.txt", build)
        self.assertIn("console-flatpaks.txt", build)
        self.assertIn("console-backports-packages.txt", build)
        # Console manifests are copied for the opt-in installer, not passed to live-build.
        self.assertNotIn('"$ROOT/linux/profiles/console-apt-packages.txt" \\\n  "$WORK/config/package-lists/', build)

    def test_console_installer_dry_run_uses_exact_manifests(self):
        env = os.environ.copy()
        env["SMARTTV_GAMING_MANIFEST_DIR"] = str(PROFILES)
        result = subprocess.run(
            ["bash", str(INSTALLER), "--print-plan"],
            env=env, check=True, text=True, capture_output=True,
        )
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 3)
        planned_apt = set(lines[0].removeprefix("APT: ").split())
        planned_backports = set(lines[1].removeprefix("BACKPORTS: ").split())
        planned_flatpak = set(lines[2].removeprefix("FLATPAK: ").split())
        self.assertEqual(planned_apt, set(packages(PROFILES / "console-apt-packages.txt")))
        self.assertEqual(planned_backports, set(packages(PROFILES / "console-backports-packages.txt")))
        self.assertEqual(planned_flatpak, set(packages(PROFILES / "console-flatpaks.txt")))
        self.assertIn("steam-installer", planned_apt)
        self.assertNotIn("steam-installer", planned_backports)

    def test_cloud_services_are_web_launchers_not_local_game_runtimes(self):
        build = BUILD.read_text(encoding="utf-8")
        backend = BACKEND.read_text(encoding="utf-8")
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('https://www.xbox.com/pt-BR/play', (ROOT / "linux/cloud-gaming/launch-cloud-game.sh").read_text())
        self.assertIn('https://play.geforcenow.com/', (ROOT / "linux/cloud-gaming/launch-cloud-game.sh").read_text())
        self.assertIn('https://cloud.boosteroid.com/', (ROOT / "linux/cloud-gaming/launch-cloud-game.sh").read_text())
        self.assertIn('smart-tv-cloud-$provider.desktop', build)
        self.assertIn('is_cloud_game', backend)
        self.assertIn("openApps(experienceProfile === 'console' ? 'local' : 'cloud')", ui)


if __name__ == "__main__":
    unittest.main()
