import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = (
    ROOT / ".github" / "workflows" / "linux.yml",
    ROOT / ".github" / "workflows" / "linux-iso.yml",
)
NODE24_MAJORS = {
    "actions/checkout": "v7",
    "actions/setup-python": "v7",
    "actions/upload-artifact": "v7",
}


class WorkflowActionVersionTests(unittest.TestCase):
    def test_javascript_actions_use_node24_compatible_majors(self):
        seen = {name: [] for name in NODE24_MAJORS}
        for workflow in WORKFLOWS:
            source = workflow.read_text(encoding="utf-8")
            for action, version in re.findall(
                r"^\s*(?:-\s*)?uses:\s*([A-Za-z0-9_./-]+)@(v[0-9]+)\s*$",
                source,
                flags=re.MULTILINE,
            ):
                if action in NODE24_MAJORS:
                    seen[action].append((workflow.name, version))

        for action, expected in NODE24_MAJORS.items():
            with self.subTest(action=action):
                self.assertTrue(seen[action], f"{action} is not referenced by the expected workflows")
                self.assertTrue(
                    all(version == expected for _, version in seen[action]),
                    f"{action} must use {expected}; found {seen[action]}",
                )

    def test_iso_workflow_uploads_all_required_artifact_groups(self):
        source = (ROOT / ".github" / "workflows" / "linux-iso.yml").read_text(encoding="utf-8")
        for name in (
            "SmartTV-OS-ISO-single",
            "SmartTV-OS-ISO-parts",
            "SmartTV-OS-7z-archive",
            "SmartTV-OS-ISO-checksums",
        ):
            with self.subTest(artifact=name):
                self.assertIn(f"name: {name}", source)
        self.assertEqual(source.count("uses: actions/upload-artifact@v7"), 4)


if __name__ == "__main__":
    unittest.main()
