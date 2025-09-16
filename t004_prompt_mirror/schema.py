"""Shared schema definitions for Prompt Mirror."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

try:  # pragma: no cover - optional dependency differences
    from pydantic import BaseModel, ValidationError
except Exception as exc:  # pragma: no cover - gracefully degrade
    raise RuntimeError("pydantic is required for schema validation") from exc


class Checks(BaseModel):
    has_role: bool
    has_task: bool
    has_inputs: bool
    has_constraints: bool
    has_format: bool
    has_examples: bool
    has_steps: bool
    has_success_criteria: bool


class Flags(BaseModel):
    ambiguous_terms: List[str]
    vague_quantifiers: List[str]
    dangling_pronouns: int


class PromptAnalysis(BaseModel):
    checks: Checks
    flags: Flags
    score: int
    notes: List[str]


def _model_validate(data: Any) -> Optional[PromptAnalysis]:
    try:
        validator = getattr(PromptAnalysis, "model_validate", None)
        if callable(validator):
            return validator(data)  # type: ignore[return-value]
        return PromptAnalysis.parse_obj(data)  # type: ignore[attr-defined]
    except ValidationError:
        return None


def _model_dump(model: PromptAnalysis) -> Dict[str, Any]:
    dumper = getattr(model, "model_dump", None)
    if callable(dumper):
        return dumper()
    return model.dict()


def validate_or_fallback(candidate: Any, fallback: Dict[str, Any]) -> Dict[str, Any]:
    """Validate candidate analysis and return fallback on failure."""
    if candidate is None:
        return fallback
    model = _model_validate(candidate)
    if model is None:
        return fallback
    data = _model_dump(model)
    data["checks"] = _model_dump(model.checks)  # type: ignore[arg-type]
    data["flags"] = _model_dump(model.flags)  # type: ignore[arg-type]
    return data
