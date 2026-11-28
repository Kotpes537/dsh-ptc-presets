"""Tests for archive reconstruction and the upstream report."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import presets
from scripts.migrate_ids import migrate


class PresetTests(unittest.TestCase):
    def test_scheduled_target_migrates_without_changing_task_instructions(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            profile = root / 'profiles/desktop'
            profile.mkdir(parents=True)
            (profile / 'cordis.patch.yml').write_text('[]\n', encoding='utf-8')
            store = root / 'storages/schedule.json'
            store.parent.mkdir()
            task = {'record': {'prompt': 'Keep the original instruction'},
                    'target': {'kind': 'new', 'create': {'agentPreset': 'ptc-workflow-fable-full'}}}
            store.write_bytes(presets.encode_json({'tables': {'tasks': {'HH': task}}}))
            migrate(profile, True)
            updated = json.loads(store.read_bytes())['tables']['tasks']['HH']
            self.assertEqual(updated['target']['create']['agentPreset'], 'fable-5-2-full')
            self.assertEqual(updated['record'], task['record'])
            before = store.read_bytes()
            migrate(profile, True)
            self.assertEqual(store.read_bytes(), before)

    def test_legacy_ids_migrate_without_renaming_plugin_paths(self):
        text = ('    - id: preset-ptc-astra\n        id: ptc-astra\n'
                'allowedAgentPresets: [ ptc-workflow-review, ptc-workflow-glm-5-3 ]\n'
                "file:///profile/local-plugins/ptc-astra/index.mjs\n")
        migrated = presets.migrate_ids(text)
        self.assertIn('preset-astra', migrated)
        self.assertIn('[ review, glm-5-3 ]', migrated)
        self.assertIn('/ptc-astra/index.mjs', migrated)
        self.assertEqual(migrated, presets.migrate_ids(migrated))

    def test_build_accepts_menu_names_and_existing_ids(self):
        with patch("sys.argv", ["presets.py", "build", "--preset", "claude sonnet 5.5",
                                "--preset", "Ревью", "--preset", "ptc-astra"]):
            with patch.object(presets, "build") as build:
                presets.main()
        self.assertEqual(build.call_args.args[3], [
            "sonnet-5-5", "review", "astra",
        ])

    def test_configuration_catalog_and_archive_references(self):
        lock, catalog = presets.spec()
        self.assertEqual(len(catalog), 54)
        self.assertEqual(len(lock["prompts"]), 19)
        self.assertFalse(any(item["id"].startswith("ptc-workflow-deepseek") for item in catalog))
        self.assertFalse(any(item["name"].startswith("PTC ") for item in catalog))
        declared_paths = {item["target"] for item in lock["prompts"]}
        folder = presets.PRESETS / "local-plugins"
        expected = set()
        for script in folder.rglob("*.mjs"):
            for name in re.findall(r"""['"](?:\./)?([a-zA-Z0-9_.-]+\.md)['"]""",
                                   script.read_text(encoding="utf-8-sig")):
                expected.add((script.parent / name).relative_to(presets.PRESETS).as_posix())
        self.assertEqual(declared_paths, expected)

    def test_reconstruction_is_checked_by_exact_hash(self):
        source = b"alpha\nomitted\nbeta\n"
        expected = b"alpha\n\nbeta\n"
        item = {
            "target": "demo.md", "path": "old.md", "lines": [[1, 1], [3, 3]],
            "separator": "\n", "sha256": hashlib.sha256(expected).hexdigest(),
        }
        self.assertEqual(presets.reconstruct(source, item), expected)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            presets.reconstruct(source.replace(b"beta", b"changed"), item)
        with self.assertRaisesRegex(ValueError, "Line range"):
            presets.reconstruct(b"", item)

    def test_workflow_teams_change_only_the_explicit_subagent_choices(self):
        _, catalog = presets.spec()
        teams = presets.teams_for(catalog)
        template = (presets.PRESETS / "ptc.patch.yml.in").read_bytes()
        self.assertEqual(presets.team_template(template, teams, []), (template, []))
        debug, names = presets.team_template(template, teams, ["debug", "debug"])
        self.assertEqual(names, ["debug"])
        self.assertIn(b"allowedAgentPresets: [ review, glm-5-3 ]", debug)
        combined, names = presets.team_template(template, teams, ["all"])
        self.assertEqual(names, list(teams))
        self.assertEqual(len(combined.splitlines()), len(template.splitlines()))
        changed = [(old, new) for old, new in zip(template.splitlines(), combined.splitlines()) if old != new]
        self.assertEqual(len(changed), 2)
        line = changed[0][1].decode()
        for team in teams.values():
            for child in team["subagents"]:
                self.assertIn(child, line)
        self.assertIn("review", line)

    def test_upstream_detects_rename_and_new_candidate(self):
        with TemporaryDirectory() as temp:
            repo = Path(temp)
            self.git(repo, "init", "-q", "--initial-branch=main")
            self.git(repo, "config", "user.name", "Preset Test")
            self.git(repo, "config", "user.email", "test@example.invalid")
            (repo / "Google").mkdir()
            (repo / "Google/old.md").write_text("Source content\n", encoding="utf-8")
            self.git(repo, "add", ".")
            self.git(repo, "commit", "-qm", "Initial")
            base = self.git(repo, "rev-parse", "HEAD")
            self.git(repo, "mv", "Google/old.md", "Google/renamed.md")
            (repo / "Google/new-model.md").write_text("New model\n", encoding="utf-8")
            (repo / "DeepSeek").mkdir()
            (repo / "DeepSeek/omitted.md").write_text("Track as other\n", encoding="utf-8")
            self.git(repo, "add", ".")
            self.git(repo, "commit", "-qm", "Update")
            report = presets.report(repo, base, self.git(repo, "rev-parse", "HEAD"), {"Google/old.md"})
            self.assertIn("R100 <code>Google/old.md</code> → <code>Google/renamed.md</code>", report)
            self.assertIn("новые или изменившиеся промпты (1)", report)
            self.assertIn("A <code>Google/new-model.md</code>", report)
            self.assertIn("Прочие изменения в архиве (1)", report)

    @staticmethod
    def git(repo, *args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


if __name__ == "__main__":
    unittest.main()
