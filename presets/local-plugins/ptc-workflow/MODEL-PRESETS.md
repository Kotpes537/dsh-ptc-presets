# PTC по моделям в DSH

В меню есть адаптированные пресеты для Claude Fable 5.2, Claude Opus 5.5, Claude Sonnet 5.5, GPT-6.2 Astra, GPT-6.2 Sol, GLM-5.3, Kimi K3, Gemini 4 Argon, Qwen 4.0 Max. Профиль также содержит новые варианты, перечисленные ниже.

Пресет задаёт инструкции. Потолок выбирается по модели и режиму главного агента в DSH даже при несовпадении имени пресета с выбранной моделью.

| Модель главного агента | High | Max |
| --- | ---: | ---: |
| Claude Fable 5.2 | 2 | 4 |
| Claude Opus 5.5 | 2 | 4 |
| GPT-6.2 Astra | 2 | 4 |
| Claude Sonnet 5.5 | 2 | 3 |
| GPT-6.2 Sol | 2 | 3 |
| DeepSeek V4.1 Flash | 2 | 3 |
| DeepSeek V4 Pro | 2 | 3 |
| GLM 5.3 | 2 | 3 |
| Kimi K3 | 2 | 3 |
| Gemini 4 Argon | 2 | 3 |
| Qwen 4.0 Max | 2 | 3 |
| Остальные модели в этих пресетах | 2 | 3 |

Потолок считается на дерево главного агента. Он действует при вызовах запуска, форка и возобновления завершившегося помощника из агента. Сообщение уже работающему помощнику использует его текущий слот. При наличии свободного места следующие независимые задания могут исполняться параллельно. Потолки этой таблицы применяются в High и Max.

Для сравнения адаптированного и Full-пресета выбери одну и ту же модель и режим. В журнале сверяй фактическую модель и режим запроса, выбранный пресет, число запусков и сообщения о достижении потолка.

## Дополнения от 26 ноября 2026 года

По умолчанию High допускает 2, Max — 3 одновременно работающих потомка. Для Fable 5.2, Opus 5.5 и GPT‑6.2 Astra Max допускает 4. Для Grok 4.7, Gemini 4 Neon и Gemini 4 Hydrogen режим `xhigh`, если его передал адаптер, получает потолок Max.

Новые пресеты:

- Claude Haiku 5.5 Full
- Claude Fable 5.1 Full
- Claude Opus 5 Full
- Claude Opus 4.8 Full
- Claude Sonnet 5 Full
- Grok 4.7 Full
- Muse Spark 1.3 Full
- MiniMax M3 Full
- Antigravity CLI
- Claude Haiku 5.5
- Claude Fable 5.1
- Claude Opus 5
- Claude Opus 4.8
- Claude Sonnet 5
- Grok 4.7
- Muse Spark 1.3
- MiniMax M3
- Gemini 3.8 Flash
- Kimi K2.6
- Qwen 3.8 Max
- Qwen 3.6 Plus
- Gemini 4 Neon
- Gemini 4 Hydrogen
- Gemini 4 Carbon
- Kimi K3.1 Pro
- Kimi K2.7 Code
- Mistral Large 4
