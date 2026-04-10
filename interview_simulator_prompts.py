# Prompt templates for AI Interview Simulator (MVP).
# Keep role / level / job description explicit so the model anchors on JD requirements.

import json
from typing import Optional

def interview_language_block(locale: str) -> str:
    """Natural language for questions, closings, evaluations, and report must match UI locale."""
    lc = (locale or "en").strip().lower()
    if lc.startswith("ru"):
        return """Language (mandatory):
- The candidate uses the Russian UI. The entire interview must be in natural Russian.
- Every candidate-facing string in your JSON ("question", closings, "summary", "strengths", "gaps", "follow_up_hint", report text fields, etc.) MUST be in Russian.
- JSON keys must remain exactly as in the schema (English).
- Technical terms: use English where it is standard in Russian IT speech (API, Docker, CI/CD); otherwise prefer Russian."""
    return """Language:
- Conduct the interview in clear English; all candidate-facing strings in English."""


SYSTEM_BASE = """You are an expert technical interviewer. You conduct structured interviews fairly.
Rules:
- Ask ONE clear question at a time (no bullet lists of multiple unrelated questions).
- Do not reveal scores to the candidate during the interview.
- If a job description (JD) is provided, you MUST tie questions and follow-ups to its requirements, stack, and responsibilities.
- Adapt difficulty to the stated seniority level.
- If an answer is shallow, ask ONE concise follow-up that probes depth on the same topic — use NEW wording and a more specific angle; never repeat the previous question verbatim or as a light paraphrase.
- Never ask two main questions in a row that target the same subtopic (e.g. two generic "tell me about testing" prompts). Vary focus across the interview.
- Output ONLY valid JSON matching the schema requested in the user message (no markdown fences)."""

# Rotating themes so consecutive questions explore different angles (reduces repetitive LLM outputs).
_QUESTION_THEMES = [
    "A concrete past situation (STAR-style): problem, your role, outcome, metrics.",
    "Technical trade-offs: two valid options and how you chose in practice.",
    "Production / incident / debugging: how you found root cause and prevented recurrence.",
    "Quality & testing: strategy, automation, what you would not compromise on.",
    "Collaboration: code review, disagreement with a peer or PM, how you resolved it.",
    "Scale, performance, or reliability: bottleneck, monitoring, or capacity.",
    "Security, privacy, or data handling relevant to the role.",
    "Delivery & prioritization under constraints (time, scope, tech debt).",
    "Deep dive into one specific tool, pattern, or stack item from the JD (if JD exists); else core skill for the role.",
    "Learning & mentorship: how you stay current or helped others grow.",
]


def _prior_assistant_questions(transcript_json: str, limit: int = 14) -> list[str]:
    try:
        arr = json.loads(transcript_json)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(arr, list):
        return []
    out: list[str] = []
    for m in arr:
        if not isinstance(m, dict):
            continue
        if m.get("role") != "assistant":
            continue
        c = (m.get("content") or "").strip()
        if not c:
            continue
        low = c.lower()
        if "completes the interview" in low or ("thank you" in low and "interview" in low):
            continue
        out.append(c)
    return out[-limit:]


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
    prior_qs = _prior_assistant_questions(transcript_json)
    if prior_qs:
        numbered = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(prior_qs))
        anti_repeat = f"""Questions you already asked the candidate (new question must be SUBSTANTIALLY different — different primary skill, scenario, or JD bullet; not a near-duplicate):
{numbered}

Hard rules:
- Do NOT ask the same question again or swap only a few words.
- If the last question was broad, make this one narrow (specific constraint, metric, or artifact), or switch theme entirely.
- If is_follow_up is true, stay on the same TOPIC as the last exchange but change the angle (e.g. numbers, failure mode, decision criteria) — still avoid repeating the previous interviewer sentence structure."""
    else:
        anti_repeat = "(No prior interviewer questions in transcript yet — open with a strong, role-appropriate starter.)"

    theme_idx = question_index % len(_QUESTION_THEMES)
    theme_hint = _QUESTION_THEMES[theme_idx]
    next_theme_idx = (question_index + 1) % len(_QUESTION_THEMES)
    next_theme = _QUESTION_THEMES[next_theme_idx]

    lang = interview_language_block(locale)

    return f"""Generate the next interview step.

{lang}

Context:
- Role: {role}
- Level: {level}
- Progress: question_index is the number of COMPLETED Q&A rounds the client already has (same as questionIndex in the request). The next JSON you return is for the following turn only.
- CRITICAL: If question_index >= {max_questions}, you MUST set "interview_complete": true and set "question" to a short closing line only — do NOT ask another interview question. (The server also enforces this.)
- Target length: between {min_questions} and {max_questions} total interviewer turns (questions + follow-ups count as turns).
- Job description (verbatim; you MUST reference it when present):
---
{jd_block}
---

Suggested focus for THIS turn (primary angle — follow it unless last_evaluation forces a follow-up on the same topic):
- {theme_hint}
- If this is NOT a follow-up, prefer this angle over repeating themes from earlier questions.
- Next turn after this one will lean toward: {next_theme} (plan ahead mentally; do not mention this to the candidate).

{anti_repeat}

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
When interview_complete is true, set question to a short closing line in the interview language (Russian UI: e.g. "Спасибо, на этом интервью завершено."; English: "Thank you, this completes the interview."). """


def build_evaluate_prompt(
    role: str,
    level: str,
    job_description: str | None,
    question: str,
    answer: str,
    locale: str = "en",
) -> str:
    jd_block = (
        job_description.strip()
        if job_description and job_description.strip()
        else "(No job description — evaluate against typical expectations for the role/level.)"
    )
    lang = interview_language_block(locale)

    return f"""Evaluate the candidate's answer.

{lang}

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
    lang = interview_language_block(locale)

    return f"""Produce the FINAL interview report for the hiring manager (not shown during the interview).

{lang}

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
