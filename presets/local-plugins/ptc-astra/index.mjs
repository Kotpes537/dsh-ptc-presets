import { readFileSync } from 'node:fs';

export const name = 'ptc-astra-system-prompt';
export const inject = ['systemPrompt'];

const prompt = readFileSync(new URL('./astra-6.2.md', import.meta.url), 'utf8');
const hostNote = 'The preceding template preserves its original Codex terminology. This session runs in DeepSeek Harness. Use the tools and communication surfaces provided by DSH and follow the permissions and project instructions of this session.';

export function apply(ctx) {
  const order = ctx.systemPrompt.getSectionOrder('DEPLOYMENT_PERSONA_PREFIX');
  ctx.effect(() => ctx.systemPrompt.section({
    name: 'ptc-astra:original',
    order: order + 1,
    text: prompt,
    interpolate: false,
  }));
  ctx.effect(() => ctx.systemPrompt.section({
    name: 'ptc-astra:host',
    order: order + 2,
    text: hostNote,
    interpolate: false,
  }));
}
