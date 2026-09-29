import logging
from typing import Any, Dict, List, Optional, Union
from pydantic import ValidationError

from app.config.settings import settings
from app.prompts import load_prompt
from app.schemas.business import BusinessProfile
from app.schemas.campaign import GeneratedContent
from app.schemas.product import FactSheet
from app.services.llm_client import get_chat_completion

logger = logging.getLogger(__name__)


def generate_content(
    fact_sheet: FactSheet,
    business: BusinessProfile,
    language: str,
    goal: str,
    llm_mock_responses: Optional[List[Union[GeneratedContent, Dict[str, Any]]]] = None,
) -> GeneratedContent:
    """
    Generates promotional content using LLM client.
    Returns GeneratedContent which self-validates (no digits, allowed placeholders only).
    Retries once on Pydantic ValidationError.
    """
    prompt_template = load_prompt("content_prompt.txt")

    target_language = language or (business.languages[0] if business.languages else "English")

    if fact_sheet.discount_percent is not None and fact_sheet.offer_price is not None:
        offer_info = (
            f"Active Offer Details:\n"
            f"- Discount: {fact_sheet.discount_percent}%\n"
            f"- Offer Price: {fact_sheet.offer_price}\n"
            f"- Valid Until: {fact_sheet.offer_valid_to}\n"
            f"Note: Use placeholders {{offer_price}}, {{discount}}, {{valid_to}} instead of raw numbers."
        )
    else:
        offer_info = "Active Offer Details: No active offer. Do NOT mention offer prices, discounts, or expiry dates."

    prompt = prompt_template.format(
        business_name=business.name,
        business_type=business.business_type,
        city=business.city,
        brand_voice=business.brand_voice,
        language=target_language,
        goal=goal,
        product_name=fact_sheet.product_name,
        product_id=fact_sheet.product_id,
        currency=fact_sheet.currency,
        offer_info=offer_info,
    )

    mock_index = 0

    def _call_llm(current_prompt: str) -> GeneratedContent:
        nonlocal mock_index
        idx = mock_index
        mock_index += 1
        messages = [
            {"role": "system", "content": "You are a creative social media content writer."},
            {"role": "user", "content": current_prompt},
        ]
        return get_chat_completion(
            messages=messages,
            response_model=GeneratedContent,
            mock_responses=llm_mock_responses,
            mock_index=idx,
        )

    try:
        return _call_llm(prompt)
    except ValidationError as e:
        logger.warning(f"Content generation Pydantic validation failed on attempt 1: {e}. Retrying once...")
        retry_prompt = (
            prompt
            + f"\n\nERROR IN PREVIOUS ATTEMPT: {e}.\n"
            f"REMINDER: Strictly NO raw digits in caption_template or cta. Use allowed placeholders {{price}}, {{offer_price}}, {{discount}}, {{valid_to}}."
        )
        return _call_llm(retry_prompt)
