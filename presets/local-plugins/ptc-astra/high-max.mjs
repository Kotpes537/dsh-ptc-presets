import { delegationLimit, effectiveEffort, resolveEffort } from './delegation-policy.mjs?v=2';

export const name = 'ptc-astra-high-max-subagents';
export const inject = ['systemPrompt', 'tools', 'llm'];

const HANDOFF = [
  'Первое поручение должно быть самодостаточным. Передай цель, ожидаемый результат, критерии проверки и все необходимые входы. Включи нужный текст ТЗ и данные прямо в поручение или укажи точные пути к уже существующим файлам. Ссылка на диалог главного агента не заменяет эти данные.',
  'Проверь доступность входов до запуска. Если файл ещё создаётся, приложи нужное содержимое или запусти проверку после готовности файла.',
  'Явно задай корень рабочей области и разрешённые пути чтения и записи. Разводи области записи. В первом поручении укажи, что при нехватке входов субагент перечисляет, чего не хватает, и спрашивает главного агента, не расширяя область поиска и не обращаясь к памяти.',
  'Используй результаты уже запущенных субагентов. При изменении режима или возобновлении не запускай ту же работу повторно.',
  'Главный агент проверяет выводы, объединяет результаты и выполняет итоговую проверку.',
  'Для короткого ответа, простой правки или шага без полезной независимой работы делегирование необязательно.',
].join(' ');

const HIGH_REVIEW = [
  'На High запускай нужную проверку сразу после чтения входов и постановки вопроса. Передай исходные данные и конкретные риски без своего вывода, если нужна независимая оценка.',
  'Для проверки по умолчанию достаточно одного помощника. Второго подключай для отдельной существенной задачи, например один сверяет расчёт, другой проверяет метод и допустимые выводы. Если пользователь задал состав, используй его в пределах потолка. Не поручай обоим заново решать весь кейс.',
  'Запроси короткий вердикт: что подтверждено, какое допущение меняет вывод и чего не хватает для проверки. В работе с данными сверяй единицу наблюдения, знаменатель, период, учёт затрат и наличие данных для статистического вывода.',
  'Перед итогом сверь выводы помощников с источником. Отличай наблюдаемую цифру от сценария на допущениях. Если расхождение меняет решение, проверь его; если данных не хватает, назови эту границу. Заверши после содержательной проверки и выполнения требований задачи.',
].join(' ');

function isLead(agent) {
  const header = agent?.session?.header;
  return header && header.origin !== 'subagent' && !(header.delegationDepth > 0);
}

export function apply(ctx) {
  const delegationTool = ({ scope, toolSet }) =>
    ['subagent', 'subagent_fork'].find(tool => ctx.tools.get(tool, scope, toolSet));

  function render(context) {
    const { agent, modelSelection } = context;
    if (!isLead(agent) || !modelSelection) return '';
    const effort = effectiveEffort(agent, modelSelection);
    const limit = delegationLimit(modelSelection, effort);
    if (limit === undefined) return '';
    const toolName = delegationTool(context);
    if (!toolName) return '';
    return `Режим рассуждения главного агента: ${effort}. Модель: ${modelSelection.model ?? 'текущая модель DSH'}. Потолок активных субагентов в этой задаче: ${limit}. Делегируй только самостоятельные части работы или проверки. Если таких частей несколько, запускай их параллельно в пределах потолка. Используй доступный инструмент ${toolName}. ${HANDOFF}${effort === 'high' ? ` ${HIGH_REVIEW}` : ''}`;
  }

  ctx.systemPrompt.context({
    name,
    order: ctx.systemPrompt.getContextOrder('SUBAGENT_DELEGATION'),
    required: true,
    interpolate: false,
    text: render,
  });

  // DSH omits the effort from a selection that uses its adapter's default.
  ctx.on('system-prompt/assemble', async (_assembly, context, next) => {
    const { agent, modelSelection, signal } = context;
    if (!isLead(agent) || !modelSelection || modelSelection.reasoningEffort !== undefined
      || !delegationTool(context)) {
      return next();
    }
    await resolveEffort(ctx.llm, agent, modelSelection, signal);
    const result = await next();
    return {
      ...result,
      contexts: result.contexts.map(item => item.name === name ? { ...item, text: render(context) } : item),
    };
  });
}
