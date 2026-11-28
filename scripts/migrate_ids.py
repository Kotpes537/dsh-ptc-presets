"""Migrate installed preset IDs, keeping a backup of every changed file."""

import argparse
from datetime import datetime
import os
from pathlib import Path

if __package__:
    from . import presets
    from .update_prompts import atomic_write
else:
    import presets
    from update_prompts import atomic_write


def migrate(profile, apply=False):
    profile = profile.resolve(strict=True)
    patch = profile / 'cordis.patch.yml'
    files = [patch]
    plugin_root = profile / 'local-plugins'
    for folder in ('ptc-astra', 'ptc-workflow', 'research-manager'):
        files.extend(path for path in (plugin_root / folder).rglob('*')
                     if path.is_file() and path.suffix in {'.mjs', '.md'})
    legacy = presets.read_json(presets.PRESETS / 'legacy-plugins.json')
    pending = []
    for path in files:
        if path.resolve() != path.absolute():
            raise ValueError(f'Linked profile path: {path}')
        old = path.read_bytes()
        relative = path.relative_to(profile).as_posix()
        if relative in legacy and presets.sha256(old) == legacy[relative]:
            new = (presets.PRESETS / relative).read_bytes()
        else:
            text = old.decode('utf-8-sig')
            migrated = presets.migrate_ids(text)
            new = old if migrated == text else migrated.encode('utf-8')
        if old != new:
            pending.append((path, old, new))
    print(f'Files to migrate: {len(pending)}')
    if not apply or not pending:
        return
    backup = profile / ('preset-id-backup-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    for path, old, _ in pending:
        saved = backup / path.relative_to(profile)
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(old)
    applied = []
    try:
        for path, old, new in pending:
            if path.read_bytes() != old:
                raise ValueError(f'Profile changed during migration: {path}')
            atomic_write(path, new)
            applied.append((path, old, new))
        for path, _, new in pending:
            if path.read_bytes() != new:
                raise ValueError(f'Failed to verify: {path}')
    except Exception:
        for path, old, new in reversed(applied):
            if path.read_bytes() == new:
                atomic_write(path, old)
        raise
    print(f'Backup: {backup}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(os.environ.get('DSH_HOME') or Path.home() / '.dsh')
    parser.add_argument('--profile-dir', type=Path, default=root / 'profiles/desktop')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    migrate(args.profile_dir, args.apply)


if __name__ == '__main__':
    main()
