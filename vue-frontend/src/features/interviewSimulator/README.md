# AI Interview Simulator (MVP)

## Architecture

- **UI**: Vue views under `src/views/InterviewSimulator*.vue` and presentational components in `components/`.
- **Interview flow**: `src/stores/interviewSimulator.js` (Pinia) — transcript, rounds, bootstrap, submit, final report.
- **Domain helpers**: `services/interviewEngine.js` (progress, guards).
- **AI boundary**: `providers/aiProvider.js` → `api/interviewApi.js` (HTTP to Flask).
- **Voice (stubs)**: `providers/voiceProvider.js` — reserved for STT/TTS.
- **Types** (JSDoc): `types.js`.

## Backend mapping

| Step | Flask endpoint | Prompt builder |
|------|----------------|----------------|
| Next question | `POST /api/interview-simulator/question` | `build_question_prompt` |
| Per-answer evaluation | `POST /api/interview-simulator/evaluate` | `build_evaluate_prompt` |
| Final report | `POST /api/interview-simulator/report` | `build_report_prompt` |

Prompt templates live in repo root: `interview_simulator_prompts.py`.

## Mock vs live AI

- **Mock**: set `INTERVIEW_SIMULATOR_MOCK=1` or omit `OPENAI_API_KEY`. Health returns `mock: true`.
- **Live**: set `OPENAI_API_KEY` and optional `INTERVIEW_SIMULATOR_MODEL` (default `gpt-4.1-mini` on server).

## File tree (feature slice)

```
features/interviewSimulator/
  README.md
  types.js
  api/interviewApi.js
  providers/aiProvider.js
  providers/voiceProvider.js
  services/interviewEngine.js
  components/*.vue
src/views/InterviewSimulatorHome.vue
src/views/InterviewSimulatorSetup.vue
src/views/InterviewSimulatorSession.vue
src/views/InterviewSimulatorResults.vue
src/stores/interviewSimulator.js
```

## TODO (next iterations)

- Wire `voiceProvider` to Web Speech API or a cloud STT/TTS provider.
- Persist sessions (localStorage or API) for history and resume.
- Stricter JSON schema validation and retries on the server.
- i18n for simulator UI strings (currently English).
- Enforce `minQuestions` / `maxQuestions` in mock mode to match production behavior.
