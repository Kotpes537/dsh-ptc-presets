"""Build the portable DSH preset package and review upstream changes."""

import argparse
from contextlib import contextmanager
import hashlib
import html
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from urllib.parse import quote
from urllib.request import urlopen
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
PRESETS = ROOT / "presets"
LOCK_FILE = PRESETS / "upstream.lock.json"
TEAM_SLOT = "                  allowedAgentPresets: [ ptc-workflow-review ]"
REVIEW_PRESET = "ptc-workflow-review"
REPOSITORY = "asgeirtj/system_prompts_leaks"
UPSTREAM = f"https://github.com/{REPOSITORY}"
SHA = re.compile(r"[a-f0-9]{40}")
ASSET_PATH = re.compile(r"local-plugins/ptc-(astra|workflow)/[a-zA-Z0-9_./-]+\.(md|mjs)")


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def encode_json(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def safe_path(path):
    return re.fullmatch(r"[a-zA-Z0-9_./-]+", path) and all(
        part not in {"", ".", ".."} for part in path.split("/")
    )


def spec():
    lock = read_json(LOCK_FILE)
    catalog = read_json(PRESETS / "catalog.json")
    if lock["repository"] != REPOSITORY or not re.fullmatch(r"[a-z0-9_-]+", lock["branch"]):
        raise ValueError("Unexpected upstream repository or branch")
    if not SHA.fullmatch(lock["reviewed_commit"]):
        raise ValueError("Upstream review checkpoint must be a commit SHA")
    by_id = {row["id"]: row["name"] for row in catalog}
    if any(not re.fullmatch(r"ptc-[a-z0-9-]+", row_id) for row_id in by_id):
        raise ValueError("Unexpected preset ID")
    if len(by_id) != len(catalog) or len(set(by_id.values())) != len(catalog):
        raise ValueError("Duplicate preset identifier or title")

    template = (PRESETS / "ptc.patch.yml.in").read_text(encoding="utf-8")
    declared = {
        row_id: json.loads(name) if name.startswith('"') else name
        for row_id, name in re.findall(r"(?m)^        id: (ptc-[a-z0-9-]+)\n        name: (.+)$", template)
    }
    if declared != by_id:
        raise ValueError("Preset labels/IDs are out of sync with the DSH declarations")
    if template.splitlines().count(TEAM_SLOT) != 2:
        raise ValueError("Expected Astra and Workflow subagent allowlists")
    teams_for(catalog)

    targets = set()
    for prompt in lock["prompts"]:
        target = prompt["target"]
        if (not ASSET_PATH.fullmatch(target) or not safe_path(target)
                or target in targets or (PRESETS / target).exists()):
            raise ValueError(f"Duplicate, invalid or already tracked target: {target}")
        if not SHA.fullmatch(prompt["revision"]) or not safe_path(prompt["path"]):
            raise ValueError(f"Invalid source locator for {target}")
        if not re.fullmatch(r"[a-f0-9]{64}", prompt["sha256"]):
            raise ValueError(f"Invalid content hash for {target}")
        if prompt["separator"] not in {"", "\n"}:
            raise ValueError(f"Invalid separator for {target}")
        targets.add(target)
    return lock, catalog


def teams_for(catalog):
    teams = read_json(PRESETS / "teams.json")
    ids = {row["id"] for row in catalog}
    if REVIEW_PRESET not in ids:
        raise ValueError("The read-only review preset must remain in the catalog")
    for name, plan in teams.items():
        children = plan["subagents"]
        member_ids = {plan["lead"], *children}
        if (name == "all" or not re.fullmatch(r"[a-z][a-z0-9-]*", name)
                or not children or len(member_ids) != len(children) + 1
                or REVIEW_PRESET in member_ids
                or not all(p.startswith("ptc-workflow-") for p in member_ids)
                or not member_ids <= ids):
            raise ValueError(f"Invalid Workflow team: {name}")
    return teams


def team_template(raw, teams, selected):
    names = list(teams) if "all" in selected else list(dict.fromkeys(selected))
    if not names:
        return raw, []
    allowed = dict.fromkeys([REVIEW_PRESET, *(p for name in names for p in teams[name]["subagents"])])
    line = "                  allowedAgentPresets: [ " + ", ".join(allowed) + " ]"
    return raw.replace(TEAM_SLOT.encode(), line.encode()), names


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], timeout=120)


def reconstruct(raw, item):
    lines = raw.splitlines(keepends=True)
    spans = item["lines"]
    if not spans or any(not 1 <= a <= b <= len(lines) for a, b in spans):
        raise ValueError(f"Line range outside source file: {item['path']}")
    content = item["separator"].encode().join(b"".join(lines[a - 1:b]) for a, b in spans)
    if sha256(content) != item["sha256"]:
        raise ValueError(f"SHA-256 mismatch for {item['target']}")
    content.decode("utf-8")
    return content


def source_content(repo, revision, path):
    if repo is not None:
        return git(repo, "show", f"{revision}:{path}")
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{quote(path)}"
    with urlopen(url, timeout=35) as response:
        content = response.read(8 * 1024 * 1024 + 1)
    if len(content) > 8 * 1024 * 1024:
        raise ValueError(f"Source file is too large: {path}")
    return content


def build(output, repo, selected_teams=()):
    lock, catalog = spec()
    files = {
        p.relative_to(PRESETS).as_posix(): p.read_bytes()
        for p in (PRESETS / "local-plugins").rglob("*")
        if p.is_file() and ASSET_PATH.fullmatch(p.relative_to(PRESETS).as_posix())
    }
    for name in ("Install-DSH-PTC.ps1", "ptc.patch.yml.in"):
        files[name] = (PRESETS / name).read_bytes()
    files["ptc.patch.yml.in"], enabled_teams = team_template(
        files["ptc.patch.yml.in"], teams_for(catalog), selected_teams
    )
    cached_sources = {}
    for item in lock["prompts"]:
        key = (item["revision"], item["path"])
        if key not in cached_sources:
            cached_sources[key] = source_content(repo, *key)
        files[item["target"]] = reconstruct(cached_sources[key], item)
    files["manifest.json"] = encode_json({
        "schemaVersion": 1,
        "dshVersion": "0.2.2-rc.5",
        "sourceRevision": lock["reviewed_commit"],
        "presets": catalog,
        "teams": enabled_teams,
        "files": [{"path": name, "sha256": sha256(data)} for name, data in sorted(files.items())],
    })
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".build-", delete=False) as tmp:
        temporary = Path(tmp.name)
    try:
        with ZipFile(temporary, "w", ZIP_DEFLATED, compresslevel=9) as package:
            for name, data in sorted(files.items()):
                package.writestr(name, data)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"{output} — {len(catalog)} presets, {len(lock['prompts'])} verified prompt files")


@contextmanager
def available_upstream(repo, branch):
    if repo is not None:
        yield repo
        return
    with tempfile.TemporaryDirectory(prefix="dsh-upstream-") as temp:
        dest = Path(temp) / "upstream.git"
        subprocess.run(
            ["git", "clone", "--bare", "--single-branch", "--branch", branch,
             "--quiet", UPSTREAM + ".git", str(dest)],
            check=True, timeout=120,
        )
        yield dest


def changes(repo, base, head):
    fields = git(repo, "diff", "--name-status", "-M", "-z", base, head).decode("utf-8").split("\0")
    fields.pop()
    changeset = []
    pos = 0
    while pos < len(fields):
        status = fields[pos]
        size = 2 if status.startswith(("R", "C")) else 1
        paths = fields[pos + 1:pos + size + 1]
        changeset.append((status, paths))
        pos += size + 1
    return changeset


def candidate(path):
    parts = PurePosixPath(path).parts
    return (len(parts) >= 2
            and parts[0] not in {"DeepSeek", ".github"}
            and path.endswith(".md")
            and not any(p.lower() in {"skills", "old", "references", "plugins", "schemas", "tools"} for p in parts[:-1])
            and parts[-1].lower() not in {"readme.md", "license.md"})


def report(repo, reviewed, head, used_sources):
    direct, candidates, other = [], [], []
    for status, paths in changes(repo, reviewed, head):
        row = (status, paths)
        if any(path in used_sources for path in paths):
            direct.append(row)
        elif any(candidate(path) for path in paths):
            candidates.append(row)
        else:
            other.append(row)

    lines = [
        "# Обновления архива промптов",
        "",
        f"Проверенный коммит: {reviewed}",
        f"Текущий коммит: {head}",
        f"[Сравнение на GitHub]({UPSTREAM}/compare/{reviewed}...{head})",
        "",
    ]
    for title, rows in (
        ("Источники, которые используются в пресетах", direct),
        ("Файлы для проверки на новые или изменившиеся промпты", candidates),
        ("Прочие изменения в архиве", other),
    ):
        lines.extend([f"## {title} ({len(rows)})", ""])
        if rows:
            lines.extend(
                "- " + html.escape(status) + " " + " → ".join(f"<code>{html.escape(p)}</code>" for p in paths)
                for status, paths in rows
            )
        else:
            lines.append("Изменений нет.")
        lines.append("")
    return "\n".join(lines)


def monitor(repo, output, compare_head):
    lock, _ = spec()
    with available_upstream(repo, lock["branch"]) as local:
        branch = compare_head or "HEAD"
        if branch not in {"HEAD", "main"} and not SHA.fullmatch(branch):
            raise ValueError("Use HEAD, main or a full comparison commit SHA")
        head = git(local, "rev-parse", f"{branch}^{{commit}}").decode().strip()
        reviewed = lock["reviewed_commit"]
        subprocess.run(["git", "-C", str(local), "merge-base", "--is-ancestor", reviewed, head],
                       check=True, timeout=30)
        content = report(local, reviewed, head, {item["path"] for item in lock["prompts"]})
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    else:
        print(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_subparsers(dest="action", required=True)
    action.add_parser("check", help="Check the preset catalog and the source lock")
    build_args = action.add_parser("build", help="Build the portable preset archive")
    build_args.add_argument("--output", type=Path, default=ROOT / "dist/DSH-PTC-portable.zip")
    build_args.add_argument("--source-repo", type=Path, help="Existing upstream clone")
    build_args.add_argument("--team", action="append", default=[],
                            choices=[*read_json(PRESETS / "teams.json"), "all"],
                            help="Allow subagent presets for one team (repeatable)")
    monitor_args = action.add_parser("upstream", help="Compare the archive with the reviewed revision")
    monitor_args.add_argument("--output", type=Path)
    monitor_args.add_argument("--source-repo", type=Path, help="Existing upstream clone instead of a fresh clone")
    monitor_args.add_argument("--head", help="Compare against a pinned revision instead of HEAD")
    opts = parser.parse_args()
    if opts.action == "build":
        build(opts.output, opts.source_repo, opts.team)
    elif opts.action == "upstream":
        monitor(opts.source_repo, opts.output, opts.head)
    else:
        lock, catalog = spec()
        print(f"{len(catalog)} presets; {len(lock['prompts'])} pinned prompt files")


if __name__ == "__main__":
    main()
