import logging
from datetime import date
from typing import List, Optional

from app.config.settings import settings
from app.prompts import load_prompt
from app.schemas.campaign import ValidationResult
from app.schemas.product import FactSheet
from app.services.llm_client import get_chat_completion
from app.tools.validators import validate_caption

logger = logging.getLogger(__name__)


def run_validation(
    caption: str,
    cta: str,
    fact_sheet: FactSheet,
    today: date,
    llm_mock_responses: Optional[List[ValidationResult]] = None,
) -> ValidationResult:
    """
    Runs multi-stage campaign validation.
    1. Deterministic validation first (validate_caption). Authoritative for factual checks.
    2. If deterministic validation passes, optionally runs LLM safety/tone check.
    LLM safety check can only ADD soft issues, never override or remove deterministic issues.
    """
    det_result = validate_caption(caption, fact_sheet, today)

    if not det_result.passed:
        return det_result

    prompt_template = load_prompt("validation_prompt.txt")
    prompt = prompt_template.format(
        business_name=fact_sheet.business_name,
        brand_voice="Warm, friendly, local",
        caption=caption,
        cta=cta,
        product_name=fact_sheet.product_name,
    )

    mock_index = 0

    def _call_llm_tone_check() -> ValidationResult:
        nonlocal mock_index
        idx = mock_index
        mock_index += 1
        messages = [
            {"role": "system", "content": "You are a brand safety and tone validator."},
            {"role": "user", "content": prompt},
        ]
        return get_chat_completion(
            messages=messages,
            response_model=ValidationResult,
            mock_responses=llm_mock_responses,
            mock_index=idx,
        )

    tone_result = _call_llm_tone_check()

    combined_issues = list(det_result.issues)
    for issue in tone_result.issues:
        if issue not in combined_issues:
            combined_issues.append(issue)

    passed = len(combined_issues) == 0
    return ValidationResult(passed=passed, issues=combined_issues)
