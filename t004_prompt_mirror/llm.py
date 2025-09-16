"""Optional OpenAI-powered analysis helpers."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

MAX_INPUT_CHARS = 1200


def _get_openai_client():  # pragma: no cover - depends on optional SDK
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        import openai
    except ImportError:
        return None

    openai.api_key = api_key
    return openai


def _safe_trim(text: str) -> str:
    if text and len(text) > MAX_INPUT_CHARS:
        return text[:MAX_INPUT_CHARS]
    return text or ""


def llm_analyze(text: str) -> Optional[Dict[str, Any]]:
    """Request an LLM-powered analysis. Returns None on error."""
    client = _get_openai_client()
    if client is None:
        return None

    payload = _build_analysis_prompt(_safe_trim(text))
    try:  # pragma: no cover - network
        response = client.ChatCompletion.create(
            model=os.getenv("PROMPT_MIRROR_MODEL", "gpt-4o-mini"),
            messages=payload,
            temperature=0.1,
            max_tokens=600,
        )
    except Exception:
        return None

    try:
        content = response["choices"][0]["message"]["content"].strip()
        return json.loads(content)
    except Exception:
        return None


def llm_rewrite(analysis: Dict[str, Any], text: str) -> Optional[str]:
    """Return an LLM-generated rewrite using the analysis."""
    client = _get_openai_client()
    if client is None:
        return None

    analysis_json = json.dumps(analysis, ensure_ascii=False)
    payload = _build_rewrite_prompt(analysis_json, _safe_trim(text))
    try:  # pragma: no cover - network
        response = client.ChatCompletion.create(
            model=os.getenv("PROMPT_MIRROR_MODEL", "gpt-4o-mini"),
            messages=payload,
            temperature=0.1,
            max_tokens=700,
        )
    except Exception:
        return None

    try:
        return response["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def _build_analysis_prompt(text: str):
    system = (
        "You are Prompt Mirror, a clarity coach. Respond with JSON that matches the schema."
    )
    user = (
        "Analyze the following prompt. Reply with JSON only using keys checks, flags, score, and notes. "
        "checks contains booleans for has_role, has_task, has_inputs, has_constraints, has_format, has_examples, has_steps, and has_success_criteria. "
        "flags.ambiguous_terms and flags.vague_quantifiers are string arrays. flags.dangling_pronouns is an integer. "
        "score is an integer 0-100. notes is an array of helpful strings."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"PROMPT:\n{text}\n" + user},
    ]


def _build_rewrite_prompt(analysis_json: str, text: str):
    system = (
        "You are Prompt Mirror, a clarity coach. Rewrite prompts into structured briefs with role, task, inputs, constraints, format, steps, success criteria, and refusal boundaries sections."
    )
    instructions = (
        "Use the provided analysis JSON to fill gaps. Avoid ambiguous language. Include numbered steps and measurable constraints."
    )
    user = (
        f"PROMPT:\n{text}\n\nANALYSIS_JSON:\n{analysis_json}\n\n{instructions}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
