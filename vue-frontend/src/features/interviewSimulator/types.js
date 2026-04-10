/**
 * @typedef {'frontend' | 'backend' | 'fullstack' | 'product_manager' | 'qa' | 'data' | 'devops' | 'software_engineer'} InterviewRole
 */

/**
 * @typedef {'junior' | 'middle' | 'senior'} InterviewLevel
 */

/**
 * @typedef {Object} JobDescription
 * @property {string} rawText
 */

/**
 * @typedef {Object} InterviewQuestion
 * @property {string} id
 * @property {string} text
 * @property {boolean} [isFollowUp]
 */

/**
 * @typedef {Object} UserAnswer
 * @property {string} questionId
 * @property {string} text
 * @property {number} [timestamp]
 */

/**
 * @typedef {Object} AnswerEvaluation
 * @property {number} relevance
 * @property {number} clarity
 * @property {number} technical_depth
 * @property {number} communication
 * @property {number} job_alignment
 * @property {string} summary
 * @property {string[]} strengths
 * @property {string[]} gaps
 * @property {boolean} needs_follow_up
 * @property {string} [follow_up_hint]
 */

/**
 * @typedef {Object} InterviewRound
 * @property {string} question
 * @property {string} answer
 * @property {AnswerEvaluation} evaluation
 */

/**
 * @typedef {Object} VacancyFit
 * @property {number} match_percent
 * @property {string} summary
 * @property {string[]} requirements_covered_well
 * @property {string[]} requirements_gaps
 * @property {string[]} topics_to_study
 */

/**
 * @typedef {Object} FinalFeedbackReport
 * @property {number} overall_score
 * @property {Record<string, number>} category_scores
 * @property {string} summary
 * @property {string[]} strengths
 * @property {string[]} weaknesses
 * @property {string[]} recommendations
 * @property {VacancyFit} vacancy_fit
 * @property {string} example_strong_answer
 */

/**
 * @typedef {Object} InterviewSessionState
 * @property {InterviewRole} role
 * @property {InterviewLevel} level
 * @property {string} jobDescription
 * @property {InterviewRound[]} rounds
 * @property {{role: 'assistant'|'user', content: string}[]} transcript
 * @property {string} currentQuestion
 * @property {FinalFeedbackReport|null} finalReport
 */

export const INTERVIEW_ROLES = [
  { id: 'frontend', label: 'Frontend' },
  { id: 'backend', label: 'Backend' },
  { id: 'fullstack', label: 'Full-stack' },
  { id: 'product_manager', label: 'Product Manager' },
  { id: 'qa', label: 'QA / Test' },
  { id: 'data', label: 'Data / Analytics' },
  { id: 'devops', label: 'DevOps / SRE' },
  { id: 'software_engineer', label: 'Software Engineer (generic)' },
];

export const INTERVIEW_LEVELS = [
  { id: 'junior', label: 'Junior' },
  { id: 'middle', label: 'Middle' },
  { id: 'senior', label: 'Senior' },
];

export const DEFAULT_MIN_QUESTIONS = 7;
export const DEFAULT_MAX_QUESTIONS = 13;
