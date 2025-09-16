# Prompt Mirror (Clarity Coach)

Prompt Mirror is a lightweight Flask application that reviews a prompt, surfaces clarity gaps, and offers a tightened rewrite. It ships with rule-based heuristics and can optionally call OpenAI models when an `OPENAI_API_KEY` is available.

## Features

- ✅ Rule-based checks for roles, tasks, inputs, constraints, format, steps, examples, and success criteria
- ⚠️ Flagging of ambiguous terms, vague quantifiers, and dangling pronouns with scoring out of 100
- 🧩 Structured rewrite template (Role, Task, Inputs, Constraints, Output Format, Steps, Success Criteria, Refusal Boundaries)
- 💾 Copy-to-clipboard, downloadable `.txt`, and inline diff view
- 🎯 Preset prompts for instant experimentation
- 🤖 Optional LLM assist (validated via Pydantic) when `OPENAI_API_KEY` is set

## Getting started

1. Install dependencies (Flask and Pydantic are required):

   ```bash
   pip install -r requirements.txt
   ```

   or install manually:

   ```bash
   pip install Flask pydantic
   ```

2. Run the development server:

   ```bash
   export FLASK_APP=t004_prompt_mirror.app
   flask run --reload
   ```

3. Open `http://127.0.0.1:5000` in your browser, paste a prompt, and review the analysis + rewrite.

### Optional OpenAI integration

If `OPENAI_API_KEY` is present (and the `openai` Python package is installed), Prompt Mirror will request an LLM analysis and rewrite. Responses are validated against the rule-based schema; if anything looks off, the app falls back to the deterministic heuristics.

Set a specific model with `PROMPT_MIRROR_MODEL` (defaults to `gpt-4o-mini`).

## Repository layout

```
t004_prompt_mirror/
  app.py           # Flask routes and preset definitions
  logic.py         # Rule-based analysis and rewrite helpers
  llm.py           # Optional OpenAI integration
  schema.py        # Pydantic schema + validators
  export.py        # Download helper
  static/ui.js     # Preset loader, copy button, diff renderer
  templates/index.html
```

## Tests

This project relies on ad-hoc checks. A quick smoke test can be run with:

```bash
python -m compileall t004_prompt_mirror
```

## License

MIT
