import json
import logging
from datetime import date
from typing import List, Optional, Union

from app.config.settings import settings
from app.prompts import load_prompt
from app.schemas.business import SalesSummary
from app.schemas.campaign import DecisionResult
from app.schemas.product import Offer, Product
from app.services.llm_client import get_chat_completion


logger = logging.getLogger(__name__)


def _validate_decision_result(
    decision: DecisionResult,
    products: List[Product],
    offers: Optional[List[Offer]],
) -> Optional[str]:
    """Validates that decision.product_id and decision.offer_id exist in inputs."""
    valid_product_ids = {p.product_id for p in products}
    if decision.product_id not in valid_product_ids:
        return f"product_id '{decision.product_id}' does not exist in available products: {sorted(valid_product_ids)}"

    if decision.offer_id:
        valid_offer_ids = {o.offer_id for o in (offers or [])}
        if decision.offer_id not in valid_offer_ids:
            return f"offer_id '{decision.offer_id}' does not exist in available offers: {sorted(valid_offer_ids)}"

    return None


def decide_product(
    sales_summary: SalesSummary,
    products: List[Product],
    goal: str,
    today: date,
    offers: Optional[List[Offer]] = None,
    llm_mock_responses: Optional[List[DecisionResult]] = None,
) -> DecisionResult:
    """
    Decides the best product and strategy for campaign using LLM.
    Validates product_id and offer_id exist in provided data, retrying once on failure.
    """
    prompt_template = load_prompt("decision_prompt.txt")

    products_data = [
        {
            "product_id": p.product_id,
            "name": p.name,
            "category": p.category,
            "stock_qty": p.stock_qty,
            "is_seasonal": p.is_seasonal,
        }
        for p in products
    ]

    offers_data = (
        [
            {
                "offer_id": o.offer_id,
                "product_id": o.product_id,
                "discount_percent": o.discount_percent,
                "valid_to": o.valid_to.isoformat(),
            }
            for o in (offers or [])
            if o.is_valid_on(today)
        ]
        if offers
        else []
    )

    prompt = prompt_template.format(
        today=today.isoformat(),
        goal=goal,
        sales_summary_json=json.dumps(sales_summary.model_dump(), indent=2),
        products_json=json.dumps(products_data, indent=2),
        offers_json=json.dumps(offers_data, indent=2),
    )

    mock_index = 0

    def _call_llm(current_prompt: str) -> DecisionResult:
        nonlocal mock_index
        idx = mock_index
        mock_index += 1
        messages = [
            {"role": "system", "content": "You are a retail marketing AI strategist."},
            {"role": "user", "content": current_prompt},
        ]
        return get_chat_completion(
            messages=messages,
            response_model=DecisionResult,
            mock_responses=llm_mock_responses,
            mock_index=idx,
        )

    decision = _call_llm(prompt)
    error_msg = _validate_decision_result(decision, products, offers)

    if error_msg is None:
        return decision

    logger.warning(
        f"Decision result validation failed on attempt 1: {error_msg}. Retrying once..."
    )

    retry_prompt = (
        prompt
        + f"\n\nERROR IN PREVIOUS ATTEMPT: {error_msg}. Please fix this and return a valid result."
    )
    decision_retry = _call_llm(retry_prompt)
    retry_error_msg = _validate_decision_result(decision_retry, products, offers)

    if retry_error_msg is None:
        return decision_retry

    raise ValueError(f"Decision agent failed after 1 retry: {retry_error_msg}")
