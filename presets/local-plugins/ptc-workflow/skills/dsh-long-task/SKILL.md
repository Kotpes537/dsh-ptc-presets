---
name: dsh-long-task
description: >-
  Helps a DeepSeek Harness agent resume a long or interrupted task with a
  checkable record of work. Use for multi-stage work, a task resumed in a new
  context, a recovery after compression, an interrupted run, or work awaiting
  results from several dependencies. Skip it for quick questions and edits
  that fit in one short turn.
---

# Продолжение длинной задачи

- Перед длительным этапом и после существенных результатов обновляй действующий список задач или файл состояния проекта, если он уже ведётся. [Что сохранить и как возобновить работу](references/checkpoint.md)
- После сжатия открой последнее состояние и точечно проверь изменённые файлы, ожидаемые результаты и незакрытые зависимости. Продолжи с первого необходимого действия.
- Совмещай независимые действия. Для зависимых шагов сначала получи результат предыдущего. Полученный результат субагента сверь с его поручением и критериями приёмки.
- Завершай работу после проверки запрошенных результатов. Для проверок с несколькими артефактами используй навык `dsh-verify-deliverable`, когда он доступен.
