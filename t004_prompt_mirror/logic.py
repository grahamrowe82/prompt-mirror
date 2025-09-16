"""Core rule-based analysis and rewriting utilities for Prompt Mirror."""
from __future__ import annotations

import re
from collections import Counter
from typing import Dict, Iterable, List

# Regular expressions for structural checks.
ROLE_PATTERN = re.compile(r"\b(?:you are|act as)\b", re.IGNORECASE)
TASK_PATTERN = re.compile(
    r"^\s*(write|draft|plan|create|design|develop|compare|summarize|analyze|build|outline|generate|evaluate|produce|compose|audit|assess)\b",
    re.IGNORECASE,
)
INPUT_PATTERN = re.compile(
    r"\b(given|using|with (?:this|the)|based on|provided|attached|from)\b",
    re.IGNORECASE,
)
CONSTRAINT_PATTERN = re.compile(
    r"(constraints?|assume|exclude|limit|deadline|budget|must|exactly|at least|no more than)",
    re.IGNORECASE,
)
FORMAT_PATTERN = re.compile(
    r"\b(output|return|respond|deliver|format|present|provide)\b.*\b(json|table|markdown|bullets?|list|outline|chart)\b",
    re.IGNORECASE | re.DOTALL,
)
EXAMPLE_PATTERN = re.compile(r"\b(example|for instance|eg:|e\.g\.)", re.IGNORECASE)
STEPS_PATTERN = re.compile(r"\b(step\s*\d+|steps|process|first|second|third|then|next|finally)\b", re.IGNORECASE)
SUCCESS_PATTERN = re.compile(
    r"\b(success(?: criteria| when)?|acceptance|definition of done|done when|complete when)\b",
    re.IGNORECASE,
)


AMBIGUOUS_TERMS: List[str] = [
    "help me with",
    "help",
    "assist",
    "optimize",
    "improve",
    "better",
    "robust",
    "flexible",
    "scalable",
    "easy",
    "efficient",
    "modern",
    "as needed",
    "user friendly",
    "marketing plan",
    "strategy",
    "nice",
]
VAGUE_QUANTIFIERS: List[str] = [
    "some",
    "many",
    "several",
    "few",
    "often",
    "quickly",
    "regularly",
    "usually",
    "sometimes",
    "various",
    "numerous",
    "couple",
    "handful",
    "soon",
    "asap",
]

AMBIGUOUS_REPLACEMENTS = {
    "help me with": "create",
    "help": "deliver",
    "assist": "provide",
    "optimize": "fine-tune",
    "improve": "strengthen",
    "better": "enhance",
    "marketing plan": "go-to-market roadmap",
    "strategy": "action blueprint",
    "user friendly": "accessible for end users",
    "modern": "contemporary",
}

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "for",
    "with",
    "within",
    "on",
    "in",
    "to",
    "into",
    "me",
    "my",
    "our",
    "your",
    "their",
    "this",
    "that",
    "these",
    "those",
    "about",
    "at",
    "by",
    "from",
    "as",
    "it",
    "is",
    "are",
    "be",
    "need",
    "needs",
    "needed",
    "please",
    "would",
    "could",
    "should",
    "can",
    "we",
    "i",
}

AMBIGUOUS_SET = {term.lower() for term in AMBIGUOUS_TERMS}
VAGUE_SET = {term.lower() for term in VAGUE_QUANTIFIERS}


def analyze_prompt(text: str) -> Dict[str, object]:
    """Analyze a prompt and return structural checks, flags, score, and notes."""
    source = text or ""
    checks = {
        "has_role": bool(ROLE_PATTERN.search(source)),
        "has_task": bool(TASK_PATTERN.search(source)),
        "has_inputs": bool(INPUT_PATTERN.search(source)),
        "has_constraints": bool(_has_constraints(source)),
        "has_format": bool(FORMAT_PATTERN.search(source)),
        "has_examples": bool(EXAMPLE_PATTERN.search(source)),
        "has_steps": bool(STEPS_PATTERN.search(source)),
        "has_success_criteria": bool(SUCCESS_PATTERN.search(source)),
    }

    ambiguous_terms = _normalize_terms(_find_terms(source, AMBIGUOUS_TERMS))
    vague_quantifiers = _find_terms(source, VAGUE_QUANTIFIERS)
    dangling_pronouns = _count_dangling_pronouns(source)

    score = _calculate_score(checks, ambiguous_terms, vague_quantifiers, dangling_pronouns)
    notes = _build_notes(checks, ambiguous_terms, vague_quantifiers, dangling_pronouns)

    return {
        "checks": checks,
        "flags": {
            "ambiguous_terms": ambiguous_terms,
            "vague_quantifiers": vague_quantifiers,
            "dangling_pronouns": dangling_pronouns,
        },
        "score": score,
        "notes": notes,
    }


def rewrite_prompt(analysis: Dict[str, object], text: str) -> str:
    """Rewrite the prompt using a structured template."""
    if analysis is None:
        raise ValueError("analysis data is required for rewrite")

    source = text or ""
    keywords = _extract_keywords(source, limit=6)
    focus_phrase = _build_focus_phrase(keywords)
    audience_phrase = _build_audience_phrase(keywords)

    role_line = _build_role_line(keywords)
    task_line = _build_task_line(focus_phrase)
    inputs_section = _build_inputs_section(focus_phrase, audience_phrase, source)
    constraints_section = _build_constraints_section()
    format_section = _build_format_section()
    steps_section = _build_steps_section(focus_phrase)
    success_section = _build_success_section()
    refusal_section = _build_refusal_section()

    sections = [
        f"Role:\n{role_line}",
        f"Task:\n{task_line}",
        inputs_section,
        constraints_section,
        format_section,
        steps_section,
        success_section,
        refusal_section,
    ]

    rewritten = "\n\n".join(sections).strip()
    rewritten = _replace_ambiguous_terms(rewritten)
    return rewritten


def _has_constraints(text: str) -> bool:
    if re.search(r"\b\d+(?:\.\d+)?\b", text):
        return True
    return bool(CONSTRAINT_PATTERN.search(text))


def _find_terms(text: str, term_list: Iterable[str]) -> List[str]:
    lowered = text.lower()
    found: List[str] = []
    for term in sorted(set(term_list), key=len, reverse=True):
        pattern = re.escape(term)
        if re.search(pattern, lowered):
            if any(term in existing for existing in found):
                continue
            found.append(term)
    return sorted(found)


def _normalize_terms(terms: List[str]) -> List[str]:
    normalized: List[str] = []
    for term in terms:
        if term == "help me with":
            term = "help"
        if term not in normalized:
            normalized.append(term)
    return normalized


def _count_dangling_pronouns(text: str) -> int:
    return len(
        re.findall(
            r"\b(?:it|this|that|they)\s+(?:is|are|was|were|should|must|can|will|need|needs)\b",
            text,
            flags=re.IGNORECASE,
        )
    )


def _calculate_score(
    checks: Dict[str, bool],
    ambiguous_terms: Iterable[str],
    vague_quantifiers: Iterable[str],
    dangling_pronouns: int,
) -> int:
    base = sum(1 for value in checks.values() if value) * 10
    penalty = 5 * len(list(ambiguous_terms)) + 2 * len(list(vague_quantifiers)) + 3 * dangling_pronouns
    score = base - penalty
    return int(max(0, min(100, score)))


def _build_notes(
    checks: Dict[str, bool],
    ambiguous_terms: List[str],
    vague_quantifiers: List[str],
    dangling_pronouns: int,
) -> List[str]:
    notes: List[str] = []
    missing_messages = {
        "has_role": "Add a clear role statement such as 'You are a specific type of expert.'",
        "has_task": "Start with an imperative task that describes the expected action.",
        "has_inputs": "Reference the inputs or source material the assistant should rely on.",
        "has_constraints": "List numeric or explicit constraints to narrow the solution space.",
        "has_format": "Specify the output format (tables, bullets, JSON, etc.).",
        "has_examples": "Provide concrete examples to anchor expectations.",
        "has_steps": "Describe the process or steps the assistant should follow.",
        "has_success_criteria": "Define what success looks like or how the result will be evaluated.",
    }

    for key, message in missing_messages.items():
        if not checks.get(key, False):
            notes.append(message)

    if ambiguous_terms:
        notes.append(
            "Clarify or replace ambiguous terms: "
            + ", ".join(sorted(ambiguous_terms))
            + "."
        )
    if vague_quantifiers:
        notes.append(
            "Quantify vague language (specify counts, ranges, or timeframes) for: "
            + ", ".join(sorted(vague_quantifiers))
            + "."
        )
    if dangling_pronouns:
        notes.append(
            "Resolve dangling pronouns (it/this/that/they) by naming the referent."
        )
    if not notes:
        notes.append("Prompt already covers the fundamentals; refine tone or examples as needed.")
    return notes


def _extract_keywords(text: str, limit: int = 6) -> List[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]+", text.lower())
    filtered = [
        token
        for token in tokens
        if token not in STOPWORDS
        and token not in AMBIGUOUS_SET
        and token not in VAGUE_SET
        and len(token) > 2
    ]
    counts = Counter(filtered)
    ordered = [word for word, _ in counts.most_common(limit)]
    return ordered


def _build_focus_phrase(keywords: List[str]) -> str:
    if not keywords:
        return "project"
    if "startup" in keywords and "marketing" in keywords:
        return "startup marketing initiative"
    if len(keywords) == 1:
        return keywords[0]
    return f"{keywords[0]} {keywords[1]}"


def _build_audience_phrase(keywords: List[str]) -> str:
    if "startup" in keywords:
        return "early-stage startup team"
    if "students" in keywords:
        return "student audience"
    if "executive" in keywords or "leadership" in keywords:
        return "executive stakeholders"
    if keywords:
        return f"stakeholders focused on {keywords[0]}"
    return "target audience"


def _build_role_line(keywords: List[str]) -> str:
    if "marketing" in keywords:
        return "You are a marketing strategist specializing in go-to-market execution for startups."
    if "product" in keywords or "design" in keywords:
        return "You are a product discovery lead who converts fuzzy requests into actionable briefs."
    if "sales" in keywords:
        return "You are a revenue operations advisor aligned with data-backed sales planning."
    if "content" in keywords or "writing" in keywords:
        return "You are an editorial architect who crafts structured content playbooks."
    if "analysis" in keywords or "analytics" in keywords:
        return "You are a data insights consultant focusing on evidence-based recommendations."
    if "engineering" in keywords or "software" in keywords:
        return "You are a delivery-focused engineering lead who defines crisp build briefs."
    return "You are a clarity coach who turns goals into precise, testable instructions."


def _build_task_line(focus_phrase: str) -> str:
    return (
        "Construct a detailed go-to-market roadmap for the "
        f"{focus_phrase}, highlighting decisions, rationales, and metrics."
    )


def _build_inputs_section(focus_phrase: str, audience_phrase: str, source: str) -> str:
    summary = _summarize_source(source)
    items = [
        f"- Primary focus: {focus_phrase}.",
        f"- Audience/context: {audience_phrase}.",
        f"- Source request recap: {summary}",
    ]
    return "Inputs (brief):\n" + "\n".join(items)


def _build_constraints_section() -> str:
    items = [
        "- Highlight exactly 3 priority initiatives with owners.",
        "- Reference a budget range of $5,000–$15,000 USD.",
        "- Assume a 30-day rollout timeline with weekly checkpoints.",
    ]
    return "Constraints:\n" + "\n".join(items)


def _build_format_section() -> str:
    lines = [
        "- Return a markdown table with columns: Step, Owner, Channel, Rationale.",
        "- Follow with bullet points covering risks, assumptions, and next actions.",
        "- End with a short paragraph summarizing success metrics.",
    ]
    return "Output Format:\n" + "\n".join(lines)


def _build_steps_section(focus_phrase: str) -> str:
    steps = [
        f"1. Clarify the audience and objectives for the {focus_phrase}.",
        "2. Audit existing assets and gaps using available inputs.",
        "3. Prioritize tactics against budget, timeline, and impact.",
        "4. Map messaging, channels, and ownership into the requested format.",
        "5. Define measurable KPIs and validation steps before concluding.",
    ]
    return "Steps:\n" + "\n".join(steps)


def _build_success_section() -> str:
    bullets = [
        "- Recommendations align with the stated constraints and audience.",
        "- Output matches the markdown table and bullet list specification.",
        "- KPIs include clear numeric targets and monitoring cadence.",
    ]
    return "Success Criteria:\n" + "\n".join(bullets)


def _build_refusal_section() -> str:
    lines = [
        "- Decline instructions that require unethical tactics or misuse of data.",
        "- Escalate if the request involves legal, medical, or financial compliance issues outside scope.",
    ]
    return "Refusal Boundaries:\n" + "\n".join(lines)


def _summarize_source(source: str) -> str:
    if not source:
        return "No original request provided."
    cleaned = re.sub(r"\s+", " ", source.strip())
    cleaned = _replace_ambiguous_terms(cleaned)
    if len(cleaned) <= 140:
        return cleaned
    return cleaned[:137] + "..."


def _replace_ambiguous_terms(text: str) -> str:
    result = text
    for term in sorted(AMBIGUOUS_TERMS, key=len, reverse=True):
        replacement = AMBIGUOUS_REPLACEMENTS.get(term, "")
        result = re.sub(re.escape(term), replacement, result, flags=re.IGNORECASE)
    result = re.sub(r"\s+\n", "\n", result)
    result = re.sub(r"\n\s+", "\n", result)
    result = re.sub(r" {2,}", " ", result)
    return result.strip()

