// high: 2, а не 1. Потолок это параллельность, а не объём работы: при 1 ежедневный
// HH-прогон упирается в ошибку при попытке запустить два независимых этапа сразу
// (промпт HH требует параллельные роли). Экономию даёт правило одного ревью и
// усилие high, а не обрезанная параллельность.
const standard = { high: 2, max: 3 };
const expanded = { high: 2, max: 4 };

const models = new Map([
  ['claudefable52', expanded],
  ['claudeopus55', expanded],
  ['gpt62astra', expanded],
  ['claudesonnet55', standard],
  ['gpt62sol', standard],
  ['deepseekflash', standard],
  ['deepseekv41flash', standard],
  ['deepseekv4pro', standard],
  ['glm53', standard],
  ['kimik3', standard],
  ['gemini4argon', standard],
  ['qwen40max', standard],
]);

// These model adapters can expose xhigh as their highest explicit effort.
const topEffortAliases = new Set(['grok47', 'gemini4neon', 'gemini4hydrogen']);

const defaults = new WeakMap();

function modelKey(model) {
  return (model ?? '').split('/').at(-1).toLowerCase()
    .replace(/[-_]20\d{2}[-_]?\d{2}[-_]?\d{2}$/, '')
    .replace(/[^a-z0-9]/g, '');
}

function cachedDefault(agent, selection) {
  const cached = defaults.get(agent);
  return cached?.provider === selection.provider && cached?.model === selection.model
    ? cached
    : undefined;
}

export function effectiveEffort(agent, selection) {
  if (!selection) return undefined;
  return selection.reasoningEffort ?? cachedDefault(agent, selection)?.effort;
}

export async function resolveEffort(llm, agent, selection, signal) {
  const cached = effectiveEffort(agent, selection);
  if (!selection || cached !== undefined || cachedDefault(agent, selection)
    || !selection.provider || !selection.model) {
    return cached;
  }

  const { provider, model } = selection;
  try {
    const info = await llm.resolveModelInfo(provider, model, signal);
    const effort = info?.reasoning?.defaultEffort;
    defaults.set(agent, { provider, model, effort });
    return effort;
  } catch {
    signal?.throwIfAborted();
    return undefined;
  }
}

export function delegationLimit(selection, effort) {
  const model = modelKey(selection?.model);
  const level = effort === 'xhigh' && topEffortAliases.has(model) ? 'max' : effort;
  if (level !== 'high' && level !== 'max') return undefined;
  return (models.get(model) ?? standard)[level];
}
