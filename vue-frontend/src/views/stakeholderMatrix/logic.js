/** Client-side mirrors of matrix helpers (for instant feedback + export). */

export function cellBucket(infl, int) {
  if (infl === 0 && int === 0) return 'minimal';
  if (infl === 0 && (int === 1 || int === 2)) return 'informed';
  if (infl === 2 && int === 2) return 'close';
  return 'satisfied';
}

export function computeConsequencesClient(placements, locale) {
  const msgs = [];
  const isEn = locale === 'en';
  const valid = {};
  Object.keys(placements || {}).forEach((rid) => {
    const p = placements[rid];
    if (!p || typeof p !== 'object') return;
    const infl = parseInt(p.infl, 10);
    const int = parseInt(p.int, 10);
    if (Number.isNaN(infl) || Number.isNaN(int)) return;
    if (infl < 0 || infl > 2 || int < 0 || int > 2) return;
    valid[rid] = [infl, int];
  });
  if (!Object.keys(valid).length) return [];

  const inClose = Object.entries(valid).filter(([, a]) => a[0] === 2 && a[1] === 2);
  if (inClose.length > 4) {
    msgs.push(
      isEn
        ? "Many people land in 'manage closely' — coordination can overload the team; clarify priorities and cadence."
        : 'Много ролей в зоне «пристальное внимание» — риск перегруза согласованиями; уточните приоритеты и каденции.',
    );
  }

  for (const [r, [infl, int]] of Object.entries(valid)) {
    const s = infl + int;
    if (r === 'cfo' && s <= 1) {
      msgs.push(
        isEn
          ? 'If finance stays in a low power / low attention area, budget surprises and approval delays are more likely.'
          : 'Если финансы остаются в зоне низкого влияния/внимания — выше риск сюрпризов с бюджетом и согласований.',
      );
    } else if (r === 'cto' && infl < 1) {
      msgs.push(
        isEn
          ? 'If technical leadership is placed with very low power, integration and scale risks can surface late.'
          : 'Если сильно занизить влияние технического руководителя, позже всплывают риски архитектуры и интеграций.',
      );
    } else if (r === 'ciso' && s <= 1) {
      msgs.push(
        isEn
          ? 'Security under-involvement on a digital product increases incident and compliance exposure.'
          : 'Слабое вовлечение security усиливает риск инцидентов и несоответствия требованиям (комплаенс, аудит).',
      );
    } else if (r === 'sponsor' && infl < 2 && int < 1) {
      msgs.push(
        isEn
          ? 'A sponsor with low interest can make it harder to protect budget and priority for the product.'
          : 'Спонсор с невысокой заинтересованностью — сложнее защищать приоритет и бюджет инициативы.',
      );
    } else if ((r === 'customer' || r === 'end_user') && infl === 0 && int === 0) {
      msgs.push(
        isEn
          ? "Users/major customers in 'minimal effort' can mean weak validation and requirements drift."
        : 'Пользователи/заказчики в зоне «минимальные усилия» — риск слабой валидации и ожиданий к продукту.',
      );
    } else if (r === 'po' && s >= 4) {
      msgs.push(
        isEn
          ? 'PO in the highest-engagement corner is plausible — watch meeting load versus backlog and trade-off time.'
        : 'PO в зоне максимального внимания — нормально, но не перегрузите встречами: оставьте время на бэклог и trade-off’ы.',
      );
    }
  }
  return [...new Set(msgs)].slice(0, 10);
}

export function computeStrengthsClient(placements, locale) {
  const isEn = locale === 'en';
  const out = [];
  const p = placements || {};
  const cfo = p.cfo;
  if (cfo && cfo.infl === 2 && cfo.int === 2) {
    out.push(
      isEn
        ? 'Finance is highly engaged — a good sign for budget decisions and business alignment.'
        : 'Финансы вовлечены — это помогает согласованиям бюджета и ожиданиям по цифрам.',
    );
  }
  if (p.cto && p.cto.infl >= 1 && p.cto.int >= 1) {
    out.push(
      isEn
        ? 'Technical leadership is in the conversation early — better for risk and scale.'
        : 'Техническое влияние заметно — это снижает риск «сюрпризов на проде».',
    );
  }
  if (p.end_user && p.end_user.int >= 1) {
    out.push(
      isEn
        ? 'User interest is visible — you create space to validate the product in reality.'
        : 'Интерес со стороны пользователей учтён — больше шансов поймать реальные сценарии.',
    );
  }
  return out.slice(0, 5);
}
