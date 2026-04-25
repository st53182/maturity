"""Prompts for problem-discovery dialog: human interviewer vs simulated user (OpenAI)."""

from __future__ import annotations

import json
from typing import Any, List, Optional

# JSON shape for /reply
REPLY_JSON_INSTRUCTION = """
Return ONLY a valid JSON object (no markdown) with exactly these keys:
{
  "reply": "string — the simulated user's next spoken reply in the interview language",
  "dialogue_complete": true or false
}

Set dialogue_complete to true when:
- The interviewer clearly ends (thanks, goodbye, enough questions), OR
- You have already given rich detail across several topics and further answers would repeat without new insight, OR
- The interviewer asks something inappropriate — reply briefly that you prefer to stick to the topic, then set dialogue_complete true.

Otherwise dialogue_complete must be false.
"""

SYNTH_JSON_INSTRUCTION = """
Return ONLY a valid JSON object (no markdown) with exactly these keys:
{
  "facts": ["short observable statements from the dialogue, no solutions"],
  "pain_points": ["user frustrations / friction, phrased as needs/problems"],
  "constraints": ["regulatory, org, tech, habit constraints mentioned"],
  "open_questions": ["what a real follow-up interview should clarify"],
  "summary": "2-4 sentences for the product team, no feature list"
}

Do not invent facts that were not implied in the transcript. If the transcript is thin, say so in summary and keep lists short.
"""


def _lang_block(locale: str) -> str:
    if (locale or "").strip().lower().startswith("ru"):
        return (
            "The interviewer uses Russian. The simulated user's replies MUST be natural Russian. "
            "If the interviewer writes in English, still reply in Russian unless they explicitly ask for English."
        )
    return (
        "The interviewer may use English or Russian. Prefer clear English for the simulated user's replies "
        "unless the interviewer is clearly conducting the interview in Russian — then reply in natural Russian."
    )


def system_persona_messenger(locale: str) -> str:
    lang = _lang_block(locale)
    return f"""You are a simulated USER (not an assistant) in a problem discovery interview.

{lang}

Context: Your organization is exploring a domestic / import-substitution messenger. The person talking to you is a product researcher — they ask questions; you answer as a user of workplace messengers.

Stay in character:
- You are a professional who uses several messengers daily (e.g. corporate chat, public apps where allowed).
- Share concrete situations: what went wrong, frequency, workarounds, emotions, costs of failure.
- You do NOT give product advice, feature lists, or architecture. If asked "what should we build", say you do not know — you can only describe your pains and context.
- You may ask one short clarifying question rarely if the interviewer's question is vague; default is to answer.
- Keep each reply under ~1200 characters unless they ask for a long story.
- Do not claim real proprietary data; plausible composite experience is fine.
"""


def build_reply_user_prompt(
    messages: List[dict[str, Any]],
    locale: str,
    max_turns: int,
    current_turn_index: int,
) -> str:
    transcript = json.dumps(messages, ensure_ascii=False)
    return f"""Interview transcript (chronological). Roles: "user" = interviewer questions, "assistant" = your past replies as the simulated user.

{transcript}

Rules:
- Produce ONLY the JSON object described in the system instructions (reply + dialogue_complete).
- current_turn_index={current_turn_index}, max_turns={max_turns}. If current_turn_index >= max_turns, set dialogue_complete to true and "reply" to a short polite closing in the interview language (no new information).
- Otherwise respond as the simulated user to the interviewer's LAST message only (the transcript already contains your previous replies).
"""


def build_synthesis_user_prompt(messages: List[dict[str, Any]], locale: str) -> str:
    transcript = json.dumps(messages, ensure_ascii=False)
    loc = "Russian" if (locale or "").strip().lower().startswith("ru") else "English"
    return f"""You are a neutral analyst. Below is a problem-discovery interview transcript (user = interviewer, assistant = simulated user).

Transcript:
{transcript}

Extract structured notes for a messenger product team. All output strings must be in {loc}.

{SYNTH_JSON_INSTRUCTION}
"""
