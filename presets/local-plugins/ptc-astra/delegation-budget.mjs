import { delegationLimit, resolveEffort } from './delegation-policy.mjs?v=2';

export const name = 'dsh-ptc-model-delegation-budget';
export const inject = ['agents', 'agentPresets', 'llm', 'subagents'];

const managedPresets = new Set([
  'astra',
  'general',
  'anthropic',
  'fable-5-2-full',
  'openai',
  'glm',
  'kimi',
  'google',
  'qwen',
  'opus-5-5-full',
  'sonnet-5-5-full',
  'astra-6-2-full',
  'sol-6-2-full',
  'glm-5-3-full',
  'kimi-k3-full',
  'gemini-4-argon-full',
  'qwen-4-0-max-full',
  'haiku-5-5-full',
  'fable-5-1-full',
  'opus-5-full',
  'opus-4-8-full',
  'sonnet-5-full',
  'grok-4-7-full',
  'muse-spark-1-3-full',
  'minimax-m3-full',
  'antigravity-cli',
  'fable-5-2',
  'opus-5-5',
  'sonnet-5-5',
  'astra-6-2',
  'sol-6-2',
  'glm-5-3',
  'kimi-k3',
  'gemini-4-argon',
  'qwen-4-0-max',
  'haiku-5-5',
  'fable-5-1',
  'opus-5',
  'opus-4-8',
  'sonnet-5',
  'grok-4-7',
  'muse-spark-1-3',
  'minimax-m3',
  'gemini-3-8-flash',
  'kimi-k2-6',
  'qwen-3-8-max',
  'qwen-3-6-plus',
  'gemini-4-neon',
  'gemini-4-hydrogen',
  'gemini-4-carbon',
  'kimi-k3-1-pro',
  'kimi-k2-7-code',
  'mistral-large-4',
  'research',
]);

const delegation = new Set(['subagent', 'subagent_fork', 'send_message']);

function managedPreset(preset) {
  return managedPresets.has(preset) || preset === 'ptc-' + 'astra' || preset === 'ptc-' + 'workflow'
    || (preset?.startsWith('ptc-workflow-') && preset !== 'ptc-workflow-' + 'review');
}

export function apply(ctx) {
  const admissions = new WeakMap();

  ctx.on('tools/execute', async (exec, next) => {
    if (!exec.agent || !delegation.has(exec.name)) return next();
    const root = ctx.subagents.rootOf(exec.agent);
    if (!managedPreset(ctx.agentPresets.composedPreset(root.ctx))) return next();

    // Serialize admission, not subagent work. Native spawn returns after the
    // child is published, so another call sees the occupied slot immediately.
    const prior = admissions.get(root) ?? Promise.resolve();
    const call = prior.then(async () => {
      exec.signal.throwIfAborted();
      const activeRequest = root.status === 'running' ? root.session.requestHeader()?.config : undefined;
      const selection = activeRequest ?? root.model.current();
      const effort = await resolveEffort(ctx.llm, root, selection, exec.signal);
      const limit = delegationLimit(selection, effort);
      if (limit === undefined) return next();

      if (exec.name === 'send_message') {
        const target = await ctx.subagents.resolveName(exec.agent, exec.arguments.agent, exec.signal);
        if (ctx.agents.get(target)) return next();
      }

      const members = await ctx.subagents.listDescendants(root.id, exec.signal);
      const active = members.filter(member => member.activity === 'running').length;
      if (active >= limit) {
        throw new Error(`Потолок делегирования для ${selection.model} в режиме ${effort}: ${limit} активных субагентов. Дождись завершения одной из текущих задач или продолжи работу имеющимися агентами.`);
      }
      exec.signal.throwIfAborted();
      return next();
    });
    admissions.set(root, call.then(() => undefined, () => undefined));
    return call;
  });
}
