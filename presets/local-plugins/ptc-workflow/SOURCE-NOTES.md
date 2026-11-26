# Источники правил PTC Workflow

Названия вариантов указывают, какой подход использован для настройки. Модель и провайдер выбираются отдельно в DSH. Общий текст и варианты написаны для инструментов DSH на основе изученных материалов. Коммит архива: `0aa4be305d75f23db32977ee255dbd430c27e2e6`.

| Вариант | Наблюдение и применение | Материал |
| --- | --- | --- |
| Claude | Самодостаточное поручение новому субагенту, независимая проверка, продолжение работы после сжатия. Для статического ревью используется профиль с ограничением инструментария. | [Claude Code Fable 5.2](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/Anthropic/claude-code/claude-code-fable-5.2.md), [сводка для сжатия](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/Anthropic/claude-code/prompts/compact.md), [официальная документация о субагентах](https://code.claude.com/docs/en/sub-agents) |
| Codex | Действовать в рамках поручения, учитывать новые уточнения, проверить входную точку и результат перед финалом. | [Astra 6.2](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/OpenAI/Codex/gpt-6.2-astra.md) |
| GLM | Перед исправлением отделить наблюдение от гипотезы и проверить причину на конкретном объекте. | [GLM ZCode Desktop](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/GLM/zcode-desktop.md) |
| Kimi | Вести состояния этапов и сочетать навыки процесса и артефакта по задаче. | [Kimi 3](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/Kimi/kimi-3.md) |
| Gemini | Изучить текущее решение, внести целевое изменение, проверить его в обычном рабочем цикле. | [Gemini CLI](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/Google/gemini-cli.md) |
| Qwen | Группировать независимые вызовы, передавать результат между зависимыми шагами. | [Qwen 4.0 Max](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/Qwen/qwen4.0-max.md) |

При запуске реальных Claude через API сохраняй неизменным уже отправленный префикс истории. Новые указания о режиме передаются через динамический контекст DSH. [Ограничения Claude Fable 5.2](https://platform.claude.com/docs/en/models/fable-5-2/whats-new-fable-5-2#editing-earlier-turns-invalidates-thinking-blocks)

Варианты используют стандартные компоненты PTC, общий блок инструкций и уже проверенное дополнение High/Max из Astra. Текущие MCP DSH доступны по действующим разрешениям. Профиль ревьюера имеет отдельный список локальных инструментов и проверку путей. Откат деклараций — удаление блока между метками `BEGIN DSH PTC WORKFLOW` и `END DSH PTC WORKFLOW` из `cordis.patch.yml`.
