"""Check and install published model prompt updates on Windows."""

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid

if __package__:
    from . import presets
else:
    import presets


APP = "DeepSeek Harness.exe"
LOCK_PATH = "presets/upstream.lock.json"
WAIT_SECONDS = 15 * 60


def installed_paths(profile, prompts):
    patch = (profile / "cordis.patch.yml").read_bytes()
    document = presets.migrate_ids(patch.decode("utf-8-sig"))
    ids = set(re.findall(r"(?m)^\s*- id: preset-([a-z][a-z0-9-]+)\s*$", document))
    if not ids:
        raise ValueError("В профиле не найдены установленные PTC-пресеты.")
    return patch, presets.prompt_targets(document, ids, prompts)


def published_hashes(commit):
    hashes = defaultdict(set)
    history = presets.git(presets.ROOT, "log", "--format=%H", commit, "--", LOCK_PATH).decode().splitlines()
    for revision in history:
        lock = json.loads(presets.git(presets.ROOT, "show", f"{revision}:{LOCK_PATH}"))
        for item in lock["prompts"]:
            hashes[item["target"]].add(item["sha256"])
    return hashes


def owned_path(root, target):
    path = root / target
    if not path.resolve().is_relative_to(root.resolve()) or path.resolve() != path.absolute():
        raise ValueError(f"Файл расположен вне ожидаемого каталога или связан с другим путём: {path}")
    return path


def get_updates(profile, commit):
    lock, _ = presets.spec()
    if (presets.ROOT / LOCK_PATH).read_bytes().replace(b"\r\n", b"\n") != presets.git(presets.ROOT, "show", f"{commit}:{LOCK_PATH}"):
        raise ValueError("Локальный список промптов отличается от списка в Git-коммите.")
    patch, installed = installed_paths(profile, lock["prompts"])
    previous = published_hashes(commit)
    updates = []
    conflicts = []
    for item in installed:
        if not item["target"].endswith(".md"):
            raise ValueError(f"Ожидался файл текста промпта: {item['target']}")
        path = owned_path(profile, item["target"])
        if not path.is_file():
            conflicts.append(f"{item['target']} (файл отсутствует)")
            continue
        current = presets.sha256(path.read_bytes())
        if current == item["sha256"]:
            continue
        if current not in previous[item["target"]]:
            conflicts.append(item["target"])
        else:
            updates.append(dict(item, before=current))
    print(f"Коммит проекта: {commit}. Сверено файлов: {len(installed)}.")
    print("Доступно к обновлению: " + (", ".join(item["target"] for item in updates) or "нет"))
    for target in conflicts:
        print(f"Локальная редакция или неизвестная версия: {target}")
    return patch, updates


def atomic_write(path, content):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_status(job, status, **details):
    atomic_write(job / "result.json", presets.encode_json({"status": status, **details}))


def powershell(script, **variables):
    exe = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    return subprocess.check_output(
        [str(exe), "-NoProfile", "-NonInteractive", "-Command", script],
        env=dict(os.environ, **variables), encoding="utf-8", timeout=20,
        creationflags=subprocess.CREATE_NO_WINDOW,
    ).strip()


def desktop_executable():
    output = powershell(
        "[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)\n"
        "Get-CimInstance Win32_Process -Filter \"Name='DeepSeek Harness.exe'\" | "
        "Where-Object { $_.ExecutablePath } | Select-Object -First 1 -ExpandProperty ExecutablePath"
    )
    if not output or not Path(output).is_file() or Path(output).name != APP:
        raise ValueError("Откройте DSH Desktop перед подготовкой обновления.")
    return Path(output)


def desktop_running(exe):
    return powershell(
        "$ErrorActionPreference = 'Stop'\n"
        "$running = Get-CimInstance Win32_Process -Filter \"Name='DeepSeek Harness.exe'\" | "
        "Where-Object { $_.ExecutablePath -eq $env:DSH_PTC_EXE }\n"
        "if ($running) { 'running' }",
        DSH_PTC_EXE=str(exe),
    ) == "running"


def queue(profile, commit, patch, updates, exe):
    root = Path(os.environ["LOCALAPPDATA"]) / "DSH-PTC-Presets" / "updates"
    job = root / uuid.uuid4().hex
    job.mkdir(parents=True)
    for item in updates:
        content = presets.reconstruct(presets.source_content(None, item["revision"], item["path"]), item)
        target = job / "new" / item["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    plan = {
        "profile": str(profile), "app": str(exe), "patch": presets.sha256(patch), "commit": commit,
        "files": [{key: item[key] for key in ("target", "before", "sha256")} for item in updates],
    }
    (job / "plan.json").write_bytes(presets.encode_json(plan))
    print(f"Отчёт обновления: {job / 'result.json'}", flush=True)
    command = subprocess.list2cmdline([sys.executable, "-B", str(Path(__file__).resolve()), "worker", str(job)])
    created = powershell(
        "$ErrorActionPreference = 'Stop'\n"
        "$startup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly "
        "-Property @{ShowWindow=[uint16]0}\n"
        "$result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
        "-Arguments @{CommandLine=$env:DSH_PTC_WORKER;ProcessStartupInformation=$startup}\n"
        "if ($result.ReturnValue -ne 0) { throw \"Worker launch failed: $($result.ReturnValue)\" }\n"
        "$result.ProcessId",
        DSH_PTC_WORKER=command,
    )
    if not created.isdigit():
        raise ValueError("Windows не подтвердил запуск процесса установки.")
    status_path = job / "result.json"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if status_path.is_file():
            status = presets.read_json(status_path)
            if status["status"] == "waiting":
                print("Обновление подготовлено. Завершите текущие задачи и выйдите из DSH через меню приложения.")
                return
            if status["status"] in {"applying", "installed"}:
                print("DSH закрыт. Ход установки записывается в отчёт.")
                return
            raise ValueError(status.get("error", status["status"]))
        time.sleep(0.2)
    raise ValueError("Процесс установки не подтвердил готовность. Проверьте отчёт.")


def apply_update(job, plan):
    profile = Path(plan["profile"])
    patch = profile / "cordis.patch.yml"
    if presets.sha256(patch.read_bytes()) != plan["patch"]:
        raise ValueError("Профиль DSH изменился после подготовки. Запустите проверку снова.")
    backup = job / "backup"
    prepared = []
    for item in plan["files"]:
        path = owned_path(profile, item["target"])
        old = path.read_bytes()
        new = owned_path(job / "new", item["target"]).read_bytes()
        if presets.sha256(old) != item["before"] or presets.sha256(new) != item["sha256"]:
            raise ValueError(f"Файл изменился после подготовки: {path}")
        saved = backup / item["target"]
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(old)
        prepared.append((path, old, new))
    applied = []
    write_status(job, "applying", backup=str(backup), commit=plan["commit"])
    try:
        if desktop_running(plan["app"]):
            raise ValueError("DSH снова открыт. Запустите проверку после завершения задач.")
        for path, old, new in prepared:
            if path.read_bytes() != old:
                raise ValueError(f"Файл изменился во время установки: {path}")
            atomic_write(path, new)
            applied.append((path, old, new))
        for path, _, new in prepared:
            if path.read_bytes() != new:
                raise ValueError(f"Итоговая сверка не прошла: {path}")
        if presets.sha256(patch.read_bytes()) != plan["patch"]:
            raise ValueError("Настройки профиля изменились во время установки.")
    except Exception:
        for path, old, new in reversed(applied):
            if path.read_bytes() == new:
                atomic_write(path, old)
        raise
    return backup


def worker(job):
    import msvcrt

    plan = presets.read_json(job / "plan.json")
    lock_name = presets.sha256(plan["profile"].casefold().encode("utf-8")) + ".lock"
    with (job.parent / lock_name).open("a+b") as mutex:
        try:
            mutex.seek(0)
            msvcrt.locking(mutex.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            write_status(job, "blocked", error="Для этого профиля уже подготовлено обновление.")
            return
        try:
            write_status(job, "waiting")
            deadline = time.monotonic() + WAIT_SECONDS
            while desktop_running(plan["app"]):
                if time.monotonic() >= deadline:
                    raise ValueError("DSH оставался открытым 15 минут. Запустите проверку снова.")
                time.sleep(2)
            backup = apply_update(job, plan)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            write_status(job, "blocked", error=str(error), backup=str(job / "backup"))
            return
        app = Path(plan["app"])
        profile = Path(plan["profile"])
        result = dict(backup=str(backup), commit=plan["commit"],
                      updated=[item["target"] for item in plan["files"]])
        write_status(job, "installed", **result, restart="pending")
        environment = dict(os.environ, DSH_HOME=str(profile.parent.parent))
        environment.pop("ELECTRON_RUN_AS_NODE", None)
        try:
            process = subprocess.Popen([str(app)], cwd=app.parent, env=environment,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
            write_status(job, "installed", **result, restart="started", pid=process.pid)
        except OSError as error:
            write_status(job, "installed", **result, restart="failed", error=str(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    for name in ("check", "queue"):
        command = modes.add_parser(name)
        command.add_argument("--profile-dir", type=Path, default=(
            Path(os.environ.get("DSH_HOME") or Path.home() / ".dsh") / "profiles" / "desktop"
        ))
    modes.add_parser("worker", help=argparse.SUPPRESS).add_argument("job", type=Path)
    args = parser.parse_args()
    if args.mode == "worker":
        worker(args.job.resolve())
        return
    profile = args.profile_dir.resolve(strict=True)
    if profile.name.casefold() != "desktop" or profile.parent.name.casefold() != "profiles":
        parser.error("Укажите фактический каталог profiles/desktop.")
    commit = presets.git(presets.ROOT, "rev-parse", "HEAD").decode().strip()
    patch, updates = get_updates(profile, commit)
    if args.mode == "queue" and updates:
            queue(profile, commit, patch, updates, desktop_executable())


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit(f"Обновление остановлено. {error}")
