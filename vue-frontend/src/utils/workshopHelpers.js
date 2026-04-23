import axios from 'axios';

export function workshopApiPath(exerciseKey) {
  return `/api/agile-training/ws/${exerciseKey}`;
}

export async function fetchWorkshopState(exerciseKey, slug, participantToken, locale) {
  const params = { locale };
  if (participantToken) params.participant_token = participantToken;
  const res = await axios.get(`${workshopApiPath(exerciseKey)}/g/${slug}/state`, { params });
  return res.data;
}

export async function saveWorkshopData(exerciseKey, slug, participantToken, data) {
  await axios.post(`${workshopApiPath(exerciseKey)}/g/${slug}/save`, {
    participant_token: participantToken,
    data,
  });
}

export async function callWorkshopCopilot({ exerciseKey, step, userText, locale, context }) {
  const res = await axios.post('/api/agile-training/ws-copilot/assist', {
    exercise_key: exerciseKey,
    step,
    user_text: userText || '',
    locale: locale || 'ru',
    context: context || '',
  });
  return res.data;
}
