import { defineStore } from 'pinia';
import { createAiProvider } from '@/features/interviewSimulator/providers/aiProvider';
import {
  DEFAULT_MAX_QUESTIONS,
  DEFAULT_MIN_QUESTIONS,
} from '@/features/interviewSimulator/types';

const ai = createAiProvider();

export const useInterviewSimulatorStore = defineStore('interviewSimulator', {
  state: () => ({
    role: 'frontend',
    level: 'middle',
    /** @type {'technical'|'problem_user'} */
    interviewMode: 'technical',
    /** @type {import('@/features/interviewSimulator/types').PersonaId} */
    persona: 'tech_employee',
    jobDescription: '',
    minQuestions: DEFAULT_MIN_QUESTIONS,
    maxQuestions: DEFAULT_MAX_QUESTIONS,
    /** UI locale for interview language ('ru' | 'en') */
    locale: 'en',
    transcript: /** @type {{role: 'assistant'|'user', content: string}[]} */ ([]),
    rounds: /** @type {import('@/features/interviewSimulator/types').InterviewRound[]} */ ([]),
    currentQuestion: '',
    lastQuestionIsFollowUp: false,
    interviewComplete: false,
    finalReport: /** @type {import('@/features/interviewSimulator/types').FinalFeedbackReport|null} */ (null),
    loading: false,
    error: /** @type {string|null} */ (null),
    serverMock: false,
  }),
  getters: {
    /** Завершённые ответы кандидата (для полосы «X / max»); совпадает с длиной `rounds`. */
    interviewerTurnsCount: (state) => state.rounds.length,
  },
  actions: {
    reset() {
      this.transcript = [];
      this.rounds = [];
      this.currentQuestion = '';
      this.interviewComplete = false;
      this.finalReport = null;
      this.error = null;
      this.loading = false;
      this.locale = 'en';
      this.interviewMode = 'technical';
      this.persona = 'tech_employee';
    },

    /**
     * @param {{ role: string, level: string, jobDescription?: string, locale?: string, interviewMode?: 'technical'|'problem_user', persona?: import('@/features/interviewSimulator/types').PersonaId }} cfg
     */
    setConfig(cfg) {
      this.role = cfg.role;
      this.level = cfg.level;
      this.jobDescription = cfg.jobDescription || '';
      this.interviewMode = cfg.interviewMode || 'technical';
      this.persona = cfg.persona || 'tech_employee';
      const raw = (cfg.locale || 'en').toString().toLowerCase();
      this.locale = raw.startsWith('ru') ? 'ru' : 'en';
    },

    async checkHealth() {
      try {
        const h = await ai.health();
        this.serverMock = !!h.mock;
      } catch {
        this.serverMock = false;
      }
    },

    _basePayload() {
      return {
        role: this.role,
        level: this.level,
        interviewMode: this.interviewMode,
        persona: this.interviewMode === 'problem_user' ? this.persona : undefined,
        jobDescription: this.jobDescription.trim() || undefined,
        minQuestions: this.minQuestions,
        maxQuestions: this.maxQuestions,
        locale: this.locale,
      };
    },

    async bootstrapFirstQuestion() {
      this.loading = true;
      this.error = null;
      try {
        const res = await ai.fetchNextQuestion({
          ...this._basePayload(),
          transcript: [],
          questionIndex: 0,
          lastEvaluation: null,
        });
        if (!res.success) throw new Error(res.error || 'Failed to load question');
        this.currentQuestion = res.question;
        this.lastQuestionIsFollowUp = !!res.is_follow_up;
        this.interviewComplete = !!res.interview_complete;
        this.transcript.push({ role: 'assistant', content: res.question });
      } catch (e) {
        this.error = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = false;
      }
    },

    /**
     * @param {string} answerText
     */
    async submitAnswer(answerText) {
      const answer = answerText.trim();
      if (!answer || !this.currentQuestion) return;

      this.loading = true;
      this.error = null;
      try {
        this.transcript.push({ role: 'user', content: answer });

        const evRes = await ai.evaluateAnswer({
          ...this._basePayload(),
          question: this.currentQuestion,
          answer,
        });
        if (!evRes.success) throw new Error(evRes.error || 'Evaluation failed');
        const evaluation = evRes.evaluation;

        this.rounds.push({
          question: this.currentQuestion,
          answer,
          evaluation,
        });

        if (this.rounds.length >= this.maxQuestions) {
          this.interviewComplete = true;
          this.currentQuestion = '';
          await this.loadFinalReport();
          if (this.error || !this.finalReport) {
            return { done: false, error: true };
          }
          return { done: true };
        }

        const qRes = await ai.fetchNextQuestion({
          ...this._basePayload(),
          transcript: [...this.transcript],
          questionIndex: this.rounds.length,
          lastEvaluation: evaluation,
        });
        if (!qRes.success) throw new Error(qRes.error || 'Next question failed');

        if (qRes.interview_complete) {
          this.interviewComplete = true;
          this.currentQuestion = '';
          await this.loadFinalReport();
          if (this.error || !this.finalReport) {
            return { done: false, error: true };
          }
          return { done: true };
        }

        this.currentQuestion = qRes.question;
        this.lastQuestionIsFollowUp = !!qRes.is_follow_up;
        this.transcript.push({ role: 'assistant', content: qRes.question });
        return { done: false };
      } catch (e) {
        this.error = e instanceof Error ? e.message : String(e);
        return { done: false, error: true };
      } finally {
        this.loading = false;
      }
    },

    async loadFinalReport() {
      this.loading = true;
      this.error = null;
      try {
        const payload = {
          ...this._basePayload(),
          rounds: this.rounds.map((r) => ({
            question: r.question,
            answer: r.answer,
            evaluation: r.evaluation,
          })),
        };
        const res = await ai.fetchFinalReport(payload);
        if (!res.success) throw new Error(res.error || 'Report failed');
        this.finalReport = res.report;
      } catch (e) {
        this.error = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = false;
      }
    },
  },
});
