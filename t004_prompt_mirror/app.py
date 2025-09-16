"""Flask application for Prompt Mirror."""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Optional

from flask import Flask, render_template, request, send_file

try:  # Local package import when running via `python -m`
    from .logic import analyze_prompt, rewrite_prompt
    from .export import to_txt
    from .schema import validate_or_fallback
    try:
        from .llm import llm_analyze, llm_rewrite
    except Exception:  # pragma: no cover - optional dependency
        llm_analyze = None
        llm_rewrite = None
except ImportError:  # pragma: no cover - support running as script
    from logic import analyze_prompt, rewrite_prompt  # type: ignore
    from export import to_txt  # type: ignore
    from schema import validate_or_fallback  # type: ignore
    try:
        from llm import llm_analyze, llm_rewrite  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        llm_analyze = None
        llm_rewrite = None


app = Flask(__name__)
MAX_INPUT_CHARS = 2000

PRESETS: List[Dict[str, str]] = [
    {
        "id": "startup_marketing",
        "label": "Startup marketing request",
        "rough": "help me with a marketing plan for a small startup",
        "polished": (
            "Role: You are a marketing strategist for early-stage founders.\n"
            "Task: Build a phased go-to-market roadmap with metrics.\n"
            "Constraints: 3 channels max, $10k test budget, launch in 30 days."
        ),
    },
    {
        "id": "feature_spec",
        "label": "Feature request with missing detail",
        "rough": "can you build something that improves onboarding for our app?",
        "polished": (
            "Role: Product discovery lead.\n"
            "Task: Draft an onboarding improvement brief with measurable outcomes.\n"
            "Constraints: 2 experiment tracks, completion rate +20% target."
        ),
    },
    {
        "id": "analysis_request",
        "label": "Data analysis ask",
        "rough": "please look at the q3 numbers and tell me what stands out",
        "polished": (
            "Role: Data insights consultant.\n"
            "Task: Produce a dashboard summary with anomalies and recommendations.\n"
            "Constraints: Focus on top 3 shifts, include % deltas and owners."
        ),
    },
]


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        result=None,
        rewrite=None,
        original_text="",
        raw_input="",
        trimmed_message=None,
        analysis_error=None,
        rewrite_error=None,
        presets=PRESETS,
        used_llm=False,
        max_chars=MAX_INPUT_CHARS,
    )


@app.route("/analyze", methods=["POST"])
def analyze():
    raw_text = request.form.get("prompt_text", "")
    trimmed_message: Optional[str] = None
    text = raw_text
    if len(raw_text) > MAX_INPUT_CHARS:
        text = raw_text[:MAX_INPUT_CHARS]
        trimmed_message = f"Input trimmed to {MAX_INPUT_CHARS} characters."

    analysis_result: Optional[Dict[str, Any]] = None
    rewrite_result: Optional[str] = None
    analysis_error: Optional[str] = None
    rewrite_error: Optional[str] = None
    used_llm = False

    fallback_analysis: Optional[Dict[str, Any]] = None
    try:
        fallback_analysis = analyze_prompt(text)
        analysis_result = fallback_analysis
    except Exception as exc:  # pragma: no cover - defensive
        analysis_error = f"Analysis failed: {exc}"
        fallback_analysis = None

    if fallback_analysis is not None and llm_analyze:
        try:
            llm_candidate = llm_analyze(text)
        except Exception as exc:  # pragma: no cover - network failure
            analysis_error = f"LLM analysis error: {exc}"
        else:
            if analysis_result is not None:
                analysis_result = validate_or_fallback(llm_candidate, analysis_result)
                used_llm = llm_candidate is not None and analysis_result is not fallback_analysis

    if analysis_result is None and fallback_analysis is not None:
        analysis_result = fallback_analysis

    if analysis_result is None:
        analysis_error = analysis_error or "Unable to analyze the prompt."

    try:
        if analysis_result is not None:
            if used_llm and llm_rewrite:
                llm_text = None
                try:
                    llm_text = llm_rewrite(analysis_result, text)
                except Exception as exc:  # pragma: no cover - network
                    rewrite_error = f"LLM rewrite error: {exc}"
                if llm_text:
                    rewrite_result = llm_text
            if rewrite_result is None:
                rewrite_result = rewrite_prompt(analysis_result, text)
    except Exception as exc:
        rewrite_error = f"Rewrite failed: {exc}"

    diff_payload = {
        "original": text,
        "rewrite": rewrite_result or "",
    }

    return render_template(
        "index.html",
        result=analysis_result,
        rewrite=rewrite_result,
        original_text=text,
        raw_input=raw_text,
        trimmed_message=trimmed_message,
        analysis_error=analysis_error,
        rewrite_error=rewrite_error,
        presets=PRESETS,
        used_llm=used_llm,
        max_chars=MAX_INPUT_CHARS,
        diff_payload=diff_payload,
    )


@app.route("/download", methods=["POST"])
def download():
    rewrite_text = request.form.get("rewrite_text", "")
    bytes_io = BytesIO(to_txt(rewrite_text))
    return send_file(
        bytes_io,
        mimetype="text/plain",
        as_attachment=True,
        download_name="prompt_mirror_rewrite.txt",
    )


if __name__ == "__main__":  # pragma: no cover
    app.run(debug=True)
