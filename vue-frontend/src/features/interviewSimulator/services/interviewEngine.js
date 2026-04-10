/**
 * Pure helpers for interview flow (no I/O).
 */

import { DEFAULT_MAX_QUESTIONS, DEFAULT_MIN_QUESTIONS } from '../types';

/**
 * @param {number} completedRounds
 * @param {number} maxQ
 */
export function progressRatio(completedRounds, maxQ = DEFAULT_MAX_QUESTIONS) {
  if (maxQ <= 0) return 0;
  return Math.min(1, completedRounds / maxQ);
}

/**
 * @param {import('../types').InterviewSessionState} state
 */
export function canStartSession(state) {
  return !!(state && state.role && state.level);
}

export function defaultMinMax() {
  return { min: DEFAULT_MIN_QUESTIONS, max: DEFAULT_MAX_QUESTIONS };
}
