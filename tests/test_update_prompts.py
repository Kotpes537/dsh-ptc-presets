"""Regression checks for applying a prepared prompt update."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import presets, update_prompts


class PromptUpdateTests(unittest.TestCase):
    def test_updates_known_files_and_preserves_local_files_and_profile(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            profile, job, plan = self.prepare_update(root)
            local_edit = profile / "local-plugins/ptc-astra/astra-6.2.md"
            local_edit.parent.mkdir(parents=True)
            local_edit.write_bytes(b"custom")
            with patch.object(update_prompts, "desktop_running", return_value=False):
                backup = update_prompts.apply_update(job, plan)
            for item in plan["files"]:
                self.assertEqual((profile / item["target"]).read_bytes(), b"published")
                self.assertEqual((backup / item["target"]).read_bytes(), b"previous")
            self.assertEqual(local_edit.read_bytes(), b"custom")
            self.assertEqual((profile / "cordis.patch.yml").read_bytes(), b"original settings")

    def test_existing_change_blocks_entire_batch(self):
        with TemporaryDirectory() as temporary:
            profile, job, plan = self.prepare_update(Path(temporary).resolve())
            first, last = [profile / item["target"] for item in plan["files"]]
            last.write_bytes(b"new local edit")
            with self.assertRaisesRegex(ValueError, "изменился после подготовки"):
                update_prompts.apply_update(job, plan)
            self.assertEqual(first.read_bytes(), b"previous")
            self.assertEqual(last.read_bytes(), b"new local edit")

    @staticmethod
    def prepare_update(root):
        profile = root / "profile"
        job = root / "job"
        targets = [
            "local-plugins/ptc-workflow/fable-5.2-system.md",
            "local-plugins/ptc-workflow/full-prompts/claude-opus-5-5.md",
        ]
        files = []
        for target in targets:
            for folder, content in ((profile, b"previous"), (job / "new", b"published")):
                path = folder / target
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            files.append({"target": target, "before": presets.sha256(b"previous"),
                          "sha256": presets.sha256(b"published")})
        (profile / "cordis.patch.yml").write_bytes(b"original settings")
        return profile, job, {"profile": str(profile), "files": files, "commit": "fixture",
                              "patch": presets.sha256(b"original settings"), "app": "fixture"}
