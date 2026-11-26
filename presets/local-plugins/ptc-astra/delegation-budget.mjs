import { delegationLimit, resolveEffort } from './delegation-policy.mjs?v=2';

export const name = 'dsh-ptc-model-delegation-budget';
export const inject = ['agents', 'agentPresets', 'llm', 'subagents'];

const delegation = new Set(['subagent', 'subagent_fork', 'send_message']);

function managedPreset(preset) {
  return preset === 'ptc-astra' || preset === 'ptc-workflow'
    || (preset?.startsWith('ptc-workflow-') && preset !== 'ptc-workflow-review');
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
