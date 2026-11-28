"""Install the private Research Manager add-on into a DSH PTC profile."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile

PACKAGE = Path(__file__).resolve().parent
HIGH_MODULE = Path('local-plugins/ptc-astra/high-max.mjs')
BASE = 'preset-fable-5-2-full'
PRESET = 'preset-research'
MARKER = '# BEGIN DSH RESEARCH MANAGER'
END = '# END DSH RESEARCH MANAGER'
ROLES = ('gemini-4-neon', 'qwen-3-8-max',
         'glm-5-3', 'review')


def render(patch, profile):
    match = re.search(r'^    - id: ' + BASE + r'\r?\n(?:(?!^    - id:|^[^ \t\r\n]).*\r?\n)*', patch, re.M)
    if not match:
        raise ValueError('Сначала установите DSH PTC Presets с --team research или --team all.')
    fable = match.group(0)
    for role in ROLES:
        if not re.search(r'^    - id: preset-' + re.escape(role) + r'\s*$', patch, re.M):
            raise ValueError(f'В профиле отсутствует {role}.')
    delegation = re.search(r'^          - &wf_delegation\r?\n(.*?)(?=^          - |^    - id:)', patch, re.M | re.S)
    if not delegation:
        raise ValueError('Отсутствует общий блок делегирования Workflow.')
    allowlist = re.search(r'allowedAgentPresets:\s*\[([^\]]+)\]', delegation[1])
    if not allowlist or not set(ROLES).issubset({x.strip() for x in allowlist[1].split(',')}):
        raise ValueError('Нужен список помощников из пакета --team research или --team all.')
    if fable.count('          - *wf_skill_filesystem') != 1 or '          - *wf_delegation' not in fable:
        raise ValueError('Конфигурация Fable отличается от поддерживаемого шаблона.')
    tools = fable[fable.index('        plugins:'):].rstrip()
    for name in ('wf_tool_schedule', 'wf_tool_plugin_manager', 'wf_tool_plugin_market'):
        tools = re.sub(r'(?m)^          - \*' + name + r'\r?\n', '', tools)
    plugin = profile / 'local-plugins' / 'research-manager'
    skills = json.dumps((plugin / 'skills').as_posix(), ensure_ascii=False)
    tools = tools.replace('          - *wf_skill_filesystem', '\n'.join([
        '          - id: skill-filesystem',
        "            name: '@deepseek-ai/dsh-skill-filesystem'",
        '            config:',
        '              watch: false',
        f'              customSkillDirs: [{skills}]',
    ]))
    uri = json.dumps((plugin / 'index.mjs').as_uri(), ensure_ascii=False)
    return '\n'.join([
        MARKER,
        '- insert:',
        f'    - id: {PRESET}',
        "      name: '@deepseek-ai/dsh-agent-preset'",
        '      config:',
        '        id: research',
        '        name: "Research Manager"',
        '        description: "Потребительские исследования, методика, анализ и ревью."',
        '        order: 2.27',
        tools,
        '          - id: research-manager-instructions',
        f'            name: {uri}',
        END,
        '',
    ])


def atomic_write(path, content):
    with NamedTemporaryFile(dir=path.parent, delete=False) as target:
        target.write(content)
        temp_path = Path(target.name)
    try:
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    dsh_home = Path(os.environ.get('DSH_HOME') or Path.home() / '.dsh')
    parser.add_argument('--profile-dir', type=Path,
                        default=dsh_home / 'profiles' / 'desktop')
    parser.add_argument('--apply', action='store_true', help='записать изменения; по умолчанию предпросмотр')
    args = parser.parse_args()
    profile = args.profile_dir.resolve()
    patch_path = profile / 'cordis.patch.yml'
    original = patch_path.read_bytes()
    patch = original.decode('utf-8-sig').replace('\r\n', '\n')
    block = render(patch, profile)
    source = PACKAGE.parents[1] / 'presets' / HIGH_MODULE
    installed_high = profile / HIGH_MODULE
    if not installed_high.is_file() or installed_high.read_bytes() != source.read_bytes():
        raise ValueError(f'Модуль High отличается от версии в этом репозитории: {installed_high}. '
                         'Сверьте базовый комплект перед установкой дополнения.')
    installed = list(re.finditer(r'^' + MARKER + r'\r?\n.*?^' + END + r'\r?$', patch, re.M | re.S))
    if installed and (len(installed) != 1 or installed[0][0].replace('\r\n', '\n').strip() != block.strip()):
        raise ValueError('В профиле уже есть другая версия Research Manager. Сверьте блок вручную.')
    if not installed and (MARKER in patch or END in patch or f'id: {PRESET}' in patch):
        raise ValueError('В профиле уже есть конфликтующий блок Research Manager.')
    data = PACKAGE / 'local-plugins' / 'research-manager'
    destinations = {}
    for relative_name in ('index.mjs', 'contract.md', 'skills/dsh-research-manager/SKILL.md',
                          'skills/dsh-research-manager/references/routes.md'):
        src = data / relative_name
        dst = profile / 'local-plugins' / 'research-manager' / relative_name
        content = src.read_bytes()
        if dst.exists() and dst.read_bytes() != content:
            raise ValueError(f'Конфликт с существующим файлом: {dst}')
        destinations[dst] = content
    pending = {dst: content for dst, content in destinations.items() if not dst.exists()}
    print(f'Профиль: {profile}')
    print(f'Новых файлов: {len(pending)}; новый пресет: {not installed}')
    if not args.apply:
        print('Предпросмотр. Для установки добавьте --apply.')
        return
    for dst, content in pending.items():
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open('xb') as output:
            output.write(content)
    if patch_path.read_bytes() != original:
        raise ValueError('Настройки изменились во время установки. Повторите предпросмотр.')
    if not installed:
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup = profile / f'cordis.patch.yml.before-research-manager-{stamp}'
        backup.write_bytes(original)
        eol = '\r\n' if b'\r\n' in original else '\n'
        payload = (eol + eol + block.replace('\r\n', '\n').replace('\n', eol)).encode('utf-8')
        atomic_write(patch_path, original + payload)
        print(f'Резервная копия: {backup}')
    print('Research Manager установлен. Откройте новую сессию после перезапуска DSH.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as error:
        raise SystemExit(f'Установка остановлена: {error}')
