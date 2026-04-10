/**
 * AI provider — thin wrapper over HTTP API (real or mock on server).
 */

import * as api from '../api/interviewApi';

/**
 * @typedef {Object} AiProvider
 * @property {(payload: object) => Promise<any>} fetchNextQuestion
 * @property {(payload: object) => Promise<any>} evaluateAnswer
 * @property {(payload: object) => Promise<any>} fetchFinalReport
 * @property {() => Promise<any>} health
 */

/** @type {AiProvider} */
export const httpAiProvider = {
  fetchNextQuestion: (payload) => api.postQuestion(payload),
  evaluateAnswer: (payload) => api.postEvaluate(payload),
  fetchFinalReport: (payload) => api.postReport(payload),
  health: () => api.getHealth(),
};

export function createAiProvider() {
  return httpAiProvider;
}
