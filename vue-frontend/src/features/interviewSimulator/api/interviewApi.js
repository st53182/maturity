import axios from 'axios';

/**
 * @param {object} body
 */
export async function postQuestion(body) {
  const { data } = await axios.post('/api/interview-simulator/question', body);
  return data;
}

/**
 * @param {object} body
 */
export async function postEvaluate(body) {
  const { data } = await axios.post('/api/interview-simulator/evaluate', body);
  return data;
}

/**
 * @param {object} body
 */
export async function postReport(body) {
  const { data } = await axios.post('/api/interview-simulator/report', body);
  return data;
}

export async function getHealth() {
  const { data } = await axios.get('/api/interview-simulator/health');
  return data;
}
