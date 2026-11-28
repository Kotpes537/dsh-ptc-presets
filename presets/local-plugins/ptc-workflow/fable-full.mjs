import { readFileSync } from 'node:fs';

import { apply as applyHighMax } from '../ptc-astra/high-max.mjs?v=5';

export const name = 'dsh-ptc-fable-full';
export const inject = ['systemPrompt', 'tools', 'llm'];

const original = readFileSync(new URL('./fable-5.2-system.md', import.meta.url), 'utf8');
const compatibility = [
  'The following archived Claude Code instructions are a behavioral reference for this DeepSeek Harness session.',
  'DeepSeek Harness supplies your actual model, date, instructions, working directory, tool schemas, and permissions. Those current values and instructions take precedence over references in the archive.',
  'Use only live DSH tools with their supplied schemas. Call them via the DSH PTC tool interface. Ignore archived paths, model identifiers, raw Anthropic tool-call markup, commands, skills, MCP servers, and agents when they refer to the captured Claude Code environment.',
  'Use DSH subagent for delegation. For an independent static review, set agent_preset to review and pass a self-contained assignment with workspace, evidence, acceptance criteria, and read-only scope. Wait via the current tool when you need the verdict.',
  'Use the current DSH skills and task checkpoint when they apply. After DSH compacts history, recover the pending step from the current summary and checkpoint. Retain the current user scope, session permissions, and project rules.',
].join('\n');

export function apply(ctx) {
  const order = ctx.systemPrompt.getSectionOrder('DEPLOYMENT_PERSONA_PREFIX');
  ctx.systemPrompt.section({
    name: 'ptc-fable-full:dsh-compatibility',
    order: order + 1,
    interpolate: false,
    text: compatibility,
  });
  ctx.systemPrompt.section({
    name: 'ptc-fable-full:archived-system',
    order: order + 2,
    interpolate: false,
    text: original,
  });
  applyHighMax(ctx);
}
