# Prompt templates for AI Interview Simulator (MVP).
# Keep role / level / job description explicit so the model anchors on JD requirements.

from typing import Optional

SYSTEM_BASE = """You are an expert technical interviewer. You conduct structured interviews fairly.
Rules:
- Ask ONE clear question at a time (no bullet lists of multiple unrelated questions).
- Do not reveal scores to the candidate during the interview.
- If a job description (JD) is provided, you MUST tie questions and follow-ups to its requirements, stack, and responsibilities.
- Adapt difficulty to the stated seniority level.
- If an answer is shallow, ask ONE concise follow-up that probes depth on the same topic.
- Output ONLY valid JSON matching the schema requested in the user message (no markdown fences)."""


def build_question_prompt(
    role: str,
    level: str,
    job_description: Optional[str],
    transcript_json: str,
    question_index: int,
    min_questions: int,
    max_questions: int,
    last_evaluation_json: str | None,
) -> str:
    jd_block = (
        job_description.strip()
        if job_description and job_description.strip()
        else "(No job description provided — use a standard interview for the role and level.)"
    )
    eval_block = last_evaluation_json or "null"
    return f"""Generate the next interview step.

Context:
- Role: {role}
- Level: {level}
- Progress: main+follow-up rounds so far (0-based index next): {question_index}
- Target length: between {min_questions} and {max_questions} total interviewer turns (questions + follow-ups count as turns).
- Job description (verbatim; you MUST reference it when present):
---
{jd_block}
---

Conversation so far (JSON array of {{\\"role\\": \\"assistant\\"|\\"user\\", \\"content\\": \\"...\\"}}):
{transcript_json}

Last answer evaluation (JSON or null):
{eval_block}

Return JSON with this exact shape:
{{
  "question": "string — the next question to ask the candidate (single question)",
  "is_follow_up": true or false,
  "interview_complete": true or false,
  "rationale_internal": "short note why this question (not shown to candidate)"
}}

Set interview_complete to true ONLY if:
- You already asked at least {min_questions} meaningful turns AND further questions add little value, OR
- You reached ~{max_questions} turns (do not exceed {max_questions}).
When interview_complete is true, set question to a short closing line like "Thank you, this completes the interview." """


def build_evaluate_prompt(
    role: str,
    level: str,
    job_description: str | None,
    question: str,
    answer: str,
) -> str:
    jd_block = (
        job_description.strip()
        if job_description and job_description.strip()
        else "(No job description — evaluate against typical expectations for the role/level.)"
    )
    return f"""Evaluate the candidate's answer.

Role: {role}
Level: {level}
Job description (use for alignment scoring when provided):
---
{jd_block}
---

Interview question:
{question}

Candidate answer:
{answer}

Return JSON ONLY:
{{
  "relevance": 0-10,
  "clarity": 0-10,
  "technical_depth": 0-10,
  "communication": 0-10,
  "job_alignment": 0-10,
  "summary": "1-2 sentences",
  "strengths": ["..."],
  "gaps": ["..."],
  "needs_follow_up": true or false,
  "follow_up_hint": "if needs_follow_up, what to probe; else empty string"
}}

If JD is missing, set job_alignment based on general role fit."""


def build_report_prompt(
    role: str,
    level: str,
    job_description: Optional[str],
    qa_block: str,
) -> str:
    jd_block = (
        job_description.strip()
        if job_description and job_description.strip()
        else "(No job description — report should focus on role/level generically.)"
    )
    return f"""Produce the FINAL interview report for the hiring manager (not shown during the interview).

Role: {role}
Level: {level}
Job description:
---
{jd_block}
---

Interview Q&A with per-answer evaluations (JSON):
{qa_block}

Return JSON ONLY:
{{
  "overall_score": 0-100,
  "category_scores": {{
    "technical_depth": 0-100,
    "communication": 0-100,
    "job_fit": 0-100,
    "problem_solving": 0-100
  }},
  "summary": "2-4 sentences overview",
  "strengths": ["..."],
  "weaknesses": ["..."],
  "recommendations": ["..."],
  "vacancy_fit": {{
    "match_percent": 0-100,
    "summary": "how well they match THIS vacancy",
    "requirements_covered_well": ["..."],
    "requirements_gaps": ["..."],
    "topics_to_study": ["..."]
  }},
  "example_strong_answer": "one concise example of a stronger answer pattern for a key gap"
}}

If JD was not provided, vacancy_fit should describe fit to the role/level instead of a specific posting."""


JSON_INSTRUCTION = "Respond with a single JSON object only. No markdown."
