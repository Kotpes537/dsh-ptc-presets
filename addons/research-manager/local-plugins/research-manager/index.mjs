import { readFileSync } from 'node:fs';

export const name = 'research';
export const inject = ['systemPrompt'];

const contract = readFileSync(new URL('./contract.md', import.meta.url), 'utf8');

export function apply(ctx) {
  ctx.systemPrompt.section({
    name: 'dsh-research-manager:contract',
    order: ctx.systemPrompt.getSectionOrder('DEPLOYMENT_PERSONA_PREFIX') + 3,
    interpolate: false,
    text: contract,
  });
}
