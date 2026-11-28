import { readFileSync } from 'node:fs';

import { apply as applyHighMax } from '../../ptc-astra/high-max.mjs?v=5';

export const name = 'dsh-ptc-full-model-prompt';
export const inject = ['systemPrompt', 'tools', 'llm'];

const promptFiles = {
  'claude-opus-5-5': 'claude-opus-5-5.md',
  'claude-sonnet-5-5': 'claude-sonnet-5-5.md',
  'openai-astra-6-2': 'openai-astra-6-2.md',
  'openai-sol-6-2': 'openai-sol-6-2.md',
  'glm-5-3': 'glm-5-3.md',
  'kimi-k3': 'kimi-k3.md',
  'google-gemini-4-argon': 'google-gemini-4-argon.md',
  'qwen-4-0-max': 'qwen-4-0-max.md',
  'claude-haiku-5-5': 'claude-haiku-5-5.md',
  'claude-fable-5-1': 'claude-fable-5-1.md',
  'claude-opus-5': 'claude-opus-5.md',
  'claude-opus-4-8': 'claude-opus-4-8.md',
  'claude-sonnet-5': 'claude-sonnet-5.md',
  'grok-4-7': 'grok-4-7.md',
  'muse-spark-1-3': 'muse-spark-1-3.md',
  'minimax-m3': 'minimax-m3.md',
  'antigravity-cli': 'antigravity-cli.md',
};

const compatibility = [
  'This is a DeepSeek Harness (DSH) session. The following archived instructions are a behavioral reference. Follow the current user request, project rules, session permissions, and live DSH context first. DSH supplies the actual model, date, workspace, available tools, and skills.',
  'Use the live DSH PTC interface and the schemas it exposes. Tool names and invocation syntax from the archive, old workspace paths, private memory paths, provider model identities, and product-specific commands refer to the original environment. Use their DSH counterparts only when available and within the current permissions.',
  'For independent work, follow the active DSH High/Max delegation guidance. Give the subagent the workspace, exact available inputs, scope, expected result, and acceptance criteria. For static review, set agent_preset to review and ask for read-only evidence. The lead owns integration and runs executable checks.',
  'If the lead needs a child result, prefer a completion notification or a single wait of at most 30 seconds, well below the enclosing PTC call timeout. Continue independent work while a child is active. Reuse the same child for follow-up and keep write scopes disjoint.',
  'Use live DSH skills when relevant. Use the current summary and workspace checkpoint to recover the next unfinished action after compaction. Verify the requested deliverable on its current version.',
].join('\n');

export function apply(ctx, config = {}) {
  const { source } = config;
  if (!Object.hasOwn(promptFiles, source)) {
    throw new Error(`Unknown DSH full prompt source: ${source}`);
  }

  const original = readFileSync(new URL(promptFiles[source], import.meta.url), 'utf8');
  const order = ctx.systemPrompt.getSectionOrder('DEPLOYMENT_PERSONA_PREFIX');
  ctx.systemPrompt.section({
    name: 'ptc-full:dsh-compatibility',
    order: order + 1,
    interpolate: false,
    text: compatibility,
  });
  ctx.systemPrompt.section({
    name: 'ptc-full:archived-system',
    order: order + 2,
    interpolate: false,
    text: original,
  });
  applyHighMax(ctx);
}
