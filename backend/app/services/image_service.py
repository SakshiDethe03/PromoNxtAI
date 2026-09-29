import logging
import os
import requests
from typing import Optional

from app.config.settings import settings
from app.schemas.business import BusinessProfile
from app.schemas.product import Product

try:
    from supabase import create_client
except ImportError:
    create_client = None

logger = logging.getLogger(__name__)


def build_image_prompt(product: Product, business: BusinessProfile) -> str:
    """
    Builds an image generation prompt using product name, product category,
    and business brand voice ONLY.
    Explicitly instructs model to include NO text, numbers, prices, or discounts.
    """
    prompt = (
        f"A professional, high-quality promotional photo of {product.name} in the category {product.category}. "
        f"Brand voice style: {business.brand_voice}. Focus purely on product aesthetics and lifestyle visual. "
        f"CRITICAL INSTRUCTION: Include NO text, NO numbers, NO prices, and NO discount offers anywhere in the visual image."
    )
    return prompt


def generate_poster_image(product: Product, business: BusinessProfile) -> str:
    """
    Generates a promotional poster image for a product via OpenRouter's Image API.
    Uploads result to Supabase Storage bucket 'campaign-images' and returns public URL.
    Returns a mock/placeholder URL if IMAGE_MOCK env flag or settings.use_sample_data is set.
    """
    env_mock = os.getenv("IMAGE_MOCK", "").lower() in ("true", "1", "yes")
    is_mock = settings.image_mock or settings.use_sample_data or env_mock

    prompt = build_image_prompt(product, business)

    if is_mock:
        logger.info(f"[IMAGE_MOCK] Skipping live OpenRouter/Supabase call. Prompt built: '{prompt}'")
        return product.image_url or "https://example.com/placeholder_poster.png"

    try:
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_site_name,
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.openrouter_image_model,
            "prompt": prompt,
            "modalities": ["image"],
            "aspect_ratio": "1:1",
            "output_format": "jpeg",
        }

        response = requests.post("https://openrouter.ai/api/v1/images", json=payload, headers=headers, timeout=120)
        response.raise_for_status()

        data = response.json()
        image_url = data["data"][0]["url"]

        if create_client is None:
            raise RuntimeError("supabase package is required for live storage upload")

        supabase = create_client(settings.supabase_url, settings.supabase_key)
        file_path = f"posters/{product.product_id}_poster.png"

        img_bytes = requests.get(image_url).content
        supabase.storage.from_("campaign-images").upload(file_path, img_bytes)

        public_url = supabase.storage.from_("campaign-images").get_public_url(file_path)
        return public_url
    except Exception as e:
        logger.error(f"Failed to generate and upload image via OpenRouter: {e}")
        raise RuntimeError(f"Image generation failed: {e}") from e
