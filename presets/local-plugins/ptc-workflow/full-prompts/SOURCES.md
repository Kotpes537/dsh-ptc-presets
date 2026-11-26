# Полные пресеты PTC в DSH

Каждый пресет использует архивный текст как инструкцию по поведению и общий блок совместимости с DSH. Модель и провайдер выбираются отдельно. Настройки High/Max, ревьюер с доступом на чтение и навыки PTC берутся из существующей конфигурации.

| Пресет | Источник | Подключённые строки | SHA-256 подключённого текста |
| --- | --- | --- | --- |
| Claude Opus 5.5 Full | [Claude Code CLI](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/Anthropic/claude-code/claude-code-opus-5.5.md) | 15–83, 89–90, 92–129, 230–338 | `e9520d422aa6a214fe828f19842a429dfbd1209c9038401bde5c93f116fb722f` |
| Claude Sonnet 5.5 Full | [Claude Code CLI](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/Anthropic/claude-code/claude-code-sonnet-5.5.md) | 13–81, 87–88, 90–125, 226–330 | `d76af8c0874049e01d1618707d0d161952e720ac84e7aeaf4382ab2f20b3f31c` |
| GPT-6.2 Astra Full | [Codex](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/OpenAI/Codex/gpt-6.2-astra.md) | 1–201 | `a2db4586952930882b3b0ecb9dff4c6d53958ecba1e10ec87dcd0b2aedb01d05` |
| GPT-6.2 Sol Full | [Codex](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/OpenAI/Codex/gpt-6.2-sol.md) | 1–201 | `229e735557dac55cec20bb1dbb4ea2b8f74aa7eaa9bad2d33e8606840ac33393` |
| GLM-5.3 Full | [ZCode Desktop](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/GLM/zcode-desktop.md) | 3–54, 67–79, 1881–1912 | `3ec40744811dbef37e3ccb84e2b850d8a1723f621d59ce0eb24eaface22b3238` |
| Kimi K3 Full | [Kimi](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/Kimi/kimi-3.md) | 1–135 | `251b4dea3feafbfbc9ff536c6883f69005e94fd01cb46b8c04006c2cdad47794` |
| Gemini 4 Argon Full | [Antigravity CLI](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/Google/antigravity/gemini-4-argon-antigravity-cli.md) | 9–232, 247–248 | `f4f91652f4bf441ce779b3895faa4c76a242e7d66f4b3c323ddc5dc8e5214326` |
| Qwen 4.0 Max Full | [Qwen](https://github.com/asgeirtj/system_prompts_leaks/blob/0aa4be305d75f23db32977ee255dbd430c27e2e6/Qwen/qwen4.0-max.md) | 1–2 | `7c86380bdd302f92e975a17141ed80276743e377bec61c156332a5a2833efe38` |

Сохранены без правок указанные строки архивных файлов. В выборку не входят захваченные рабочие пути, параметры сеанса и схемы инструментов поставщиков. Для Google взят промпт CLI Antigravity на Gemini 4 Argon. В архиве Qwen 4.0 Max до метаданных запуска есть одна инструкция о порядке вызова инструментов.

Пресет Fable 5.2 Full установлен отдельно и описан в [FABLE-SOURCE.md](../FABLE-SOURCE.md). Название «Astra» относится к ранее установленному пресету, новый «GPT-6.2 Astra Full» использует текст Codex из указанного в таблице архива и инструменты PTC Workflow.

Удаление блока между метками BEGIN и END DSH PTC FULL MODEL VARIANTS в cordis.patch.yml убирает только восемь новых пресетов.

## Дополнения от 26 ноября 2026 года

Снимок 74761cc521a4ea73a603b54e7465e057de8ced19. Порядок строк сохранён. Содержимое рабочих сеансов, данные пользователя и каталоги инструментов поставщиков исключены.

| Пресет | Источник | Строки архива | SHA-256 |
| --- | --- | --- | --- |
| Claude Haiku 5.5 Full | [Источник](https://github.com/asgeirtj/system_prompts_leaks/blob/74761cc521a4ea73a603b54e7465e057de8ced19/Anthropic/claude-code/claude-code-haiku-5.5.md) | 3–5, 9–18, 107–127, 228–239 | `f0b454f35719e73f59fa1c7f7ec0b729f18e8fa39877acfcf91d1d69aa4b3d26` |
| Claude Fable 5.1 Full | [Источник](https://github.com/asgeirtj/system_prompts_leaks/blob/74761cc521a4ea73a603b54e7465e057de8ced19/Anthropic/claude-code/claude-code-fable-5.1.md) | 15–17, 21–30, 123–163, 264–275 | `7ebb69d791a10fcf3cc8b8d77771e44783f9ba0f7be336e3ff7261184a8f70c1` |
| Claude Opus 5 Full | [Источник](https://github.com/asgeirtj/system_prompts_leaks/blob/74761cc521a4ea73a603b54e7465e057de8ced19/Anthropic/claude-code/claude-code-opus-5.md) | 15–17, 21–30, 119–143, 244–255 | `eb8ee9d5e0b3d26f9a3aeb66577f2f7730fb35e08351d2f1c3df1dc4b2996182` |
| Claude Opus 4.8 Full | [Источник](https://github.com/asgeirtj/system_prompts_leaks/blob/74761cc521a4ea73a603b54e7465e057de8ced19/Anthropic/claude-code/claude-code-opus-4.8.md) | 15–17, 21–30, 119–129, 230–241 | `f5d12f457c6f03c2c53e6afb1f4d31f7f8e2c4019f4f90a494957042a75f55ac` |
| Claude Sonnet 5 Full | [Источник](https://github.com/asgeirtj/system_prompts_leaks/blob/74761cc521a4ea73a603b54e7465e057de8ced19/Anthropic/claude-code/claude-code-sonnet-5.md) | 15–17, 22–70, 118–134, 284–294, 403–414 | `5ea40e0a00aa833765ed67c3ae51a6a8eb3cbb9a3730ab073db333cfe0231532` |
| Grok 4.7 Full | [Источник](https://github.com/asgeirtj/system_prompts_leaks/blob/74761cc521a4ea73a603b54e7465e057de8ced19/xAI/grok-4.7-cli.md) | 37–57, 83–133, 141–153 | `96d29de89960683bae620b25920c15455558c59fb9f31bbd2fd20a7fe9bb5873` |
| Muse Spark 1.3 Full | [Источник](https://github.com/asgeirtj/system_prompts_leaks/blob/74761cc521a4ea73a603b54e7465e057de8ced19/Meta/muse-code/muse-spark-1.3-muse-code.md) | 1546–1662 | `f60083043efa6711cb22edf91f2f32db6928b4e803dbc0ef432c1f188eddf7c0` |
| MiniMax M3 Full | [Источник](https://github.com/asgeirtj/system_prompts_leaks/blob/74761cc521a4ea73a603b54e7465e057de8ced19/MiniMax/minimax-m3-mavis.md) | 1–59, 63–86 | `588a6461a92e242e2c98f3279c710deeebfa27e13324693527651e324e36da36` |
| Antigravity CLI | [Источник](https://github.com/asgeirtj/system_prompts_leaks/blob/74761cc521a4ea73a603b54e7465e057de8ced19/Google/antigravity/antigravity-cli.md) | 94–115, 140–157, 178–198 | `9318fe8aed480bc9638f20203ec84ba4cb464df54f3bdc59d5a50102cacf0848` |
