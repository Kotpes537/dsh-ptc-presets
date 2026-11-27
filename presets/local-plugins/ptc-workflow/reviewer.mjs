import { realpathSync } from 'node:fs';
import { isAbsolute, relative, resolve, sep } from 'node:path';

export const name = 'dsh-ptc-workflow-review';
export const inject = ['systemPrompt', 'tools'];

const reviewTools = new Set(['read', 'grep', 'glob']);
const allowedTransport = new Set(['run_code', 'working_directory']);

function checkReviewCall({ name, arguments: args, agent }) {
  if (allowedTransport.has(name)) return;
  if (!reviewTools.has(name)) return 'The review preset permits workspace reads only. Ask the lead to perform this operation.';

  const cwd = agent?.session?.header?.cwd;
  if (!cwd) return 'The review workspace is unavailable.';
  const input = name === 'read' ? args?.file_path : (args?.path ?? '.');
  if (typeof input !== 'string' || input.length === 0) return 'Provide a path in the review workspace.';

  try {
    const root = realpathSync(cwd);
    const target = realpathSync(resolve(root, input));
    const offset = relative(root, target);
    if (isAbsolute(offset) || offset === '..' || offset.startsWith('..' + sep)) {
      return 'The requested path resolves outside the review workspace.';
    }
  } catch {
    return 'The path is unavailable. Ask the lead for the exact path or missing input.';
  }
}

export function apply(ctx) {
  ctx.tools.guard(checkReviewCall);
  ctx.systemPrompt.section({
    name: 'ptc-workflow:review',
    order: ctx.systemPrompt.getSectionOrder('DEPLOYMENT_PERSONA_PREFIX') + 1,
    interpolate: false,
    text: [
      'You are an independent, read-only reviewer in DeepSeek Harness.',
      'Use read, glob and grep inside your initial workspace to compare the available evidence with the supplied acceptance criteria.',
      'If input is missing, report the specific missing path or criterion to the lead.',
      'Report actionable findings with path, observable evidence, impact and a suggested correction. Distinguish static inspection from any test result supplied by the lead. Ask the lead to run required checks.',
      'For architecture findings, trace concrete imports or call sites that form a dependency cycle or rely on another module’s implementation details. Explain what change would force edits across those sites, and suggest a narrower interface only when it reduces that coupling.',
      'Return a concise result that the lead can verify and integrate.',
    ].join(' '),
  });
}
