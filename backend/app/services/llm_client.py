import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel

from app.config.settings import settings
from app.schemas.campaign import DecisionResult, GeneratedContent, ValidationResult

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _build_default_mock(response_model: Type[T]) -> T:
    """Builds default mock response for a given model type if mock mode is active."""
    if response_model == DecisionResult:
        return DecisionResult(
            product_id="prod_001",
            reason="Default mock decision",
            strategy="boost_bestseller",
            offer_id=None,
        )  # type: ignore
    elif response_model == GeneratedContent:
        return GeneratedContent(
            caption_template="Treat yourself to fresh treats! Special offer at {price} INR!",
            cta="Order on WhatsApp now",
            hashtags=["#FreshCakes"],
            creative_brief="Cake photo",
        )  # type: ignore
    elif response_model == ValidationResult:
        return ValidationResult(passed=True, issues=[])  # type: ignore
    else:
        return response_model.model_construct()  # type: ignore


def get_chat_completion(
    messages: List[Dict[str, str]],
    response_model: Type[T],
    mock_responses: Optional[List[Union[T, Dict[str, Any]]]] = None,
    mock_index: int = 0,
) -> T:
    """
    Executes a structured chat completion call via OpenRouter API.
    Parses output into the specified Pydantic response_model.
    Supports mock_responses or settings.llm_mock for testing.
    """
    if mock_responses is not None and len(mock_responses) > 0:
        idx = min(mock_index, len(mock_responses) - 1)
        item = mock_responses[idx]
        if isinstance(item, response_model):
            return item
        elif isinstance(item, dict):
            return response_model(**item)

    if settings.llm_mock:
        return _build_default_mock(response_model)

    from openai import OpenAI

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
        default_headers={
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_site_name,
        },
    )

    completion = client.beta.chat.completions.parse(
        model=settings.openrouter_text_model,
        messages=messages,
        response_format=response_model,
        max_tokens=1024,
    )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("Failed to parse structured output from OpenRouter response.")
    return parsed
