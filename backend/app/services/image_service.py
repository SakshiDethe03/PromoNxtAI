import logging
import os
import requests
from typing import Optional, Tuple

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


def generate_poster_image(product: Product, business: BusinessProfile) -> Tuple[str, bool]:
    """
    Generates a promotional poster image for a product via OpenRouter's Image API.
    Uploads result to Supabase Storage bucket 'campaign-images' and returns (public_url, image_is_generated).
    Returns (product.image_url, False) if IMAGE_MOCK env flag or settings.image_mock is set,
    or on transient image generation failure fallback.
    Surfaces non-transient configuration errors (e.g. 401, 402, 403).
    """
    env_mock = os.getenv("IMAGE_MOCK", "").lower() in ("true", "1", "yes")
    is_mock = settings.image_mock or env_mock

    prompt = build_image_prompt(product, business)

    if is_mock:
        logger.info(f"[IMAGE_MOCK] Skipping live OpenRouter/Supabase call. Prompt built: '{prompt}'")
        return (product.image_url or "https://example.com/placeholder_poster.png", False)

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

    try:
        response = requests.post("https://openrouter.ai/api/v1/images", json=payload, headers=headers, timeout=120)
        
        if response.status_code in (401, 402, 403) or (400 <= response.status_code < 500):
            response.raise_for_status()

        response.raise_for_status()

        data = response.json()
        image_url = data["data"][0]["url"]

        try:
            if create_client is not None:
                supabase = create_client(settings.supabase_url, settings.supabase_key)
                file_path = f"posters/{product.product_id}_poster.jpg"
                img_bytes = requests.get(image_url).content
                supabase.storage.from_("campaign-images").upload(
                    file_path, img_bytes, file_options={"upsert": "true"}
                )
                return (supabase.storage.from_("campaign-images").get_public_url(file_path), True)
        except Exception as upload_err:
            logger.warning(f"Supabase upload failed, returning direct image URL: {upload_err}")
            return (image_url, True)

        return (image_url, True)

    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as transient_err:
        status_code = "N/A"
        logger.warning(
            f"Image generation failed ({status_code}): {transient_err}. "
            f"Falling back to product.image_url — this is a STOCK PHOTO, not an AI-generated image."
        )
        fallback_url = product.image_url if (product and product.image_url) else "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=800&auto=format&fit=crop"
        return (fallback_url, False)
    except requests.exceptions.HTTPError as http_err:
        if http_err.response is not None and 500 <= http_err.response.status_code < 600:
            status_code = http_err.response.status_code
            logger.warning(
                f"Image generation failed ({status_code}): {http_err}. "
                f"Falling back to product.image_url — this is a STOCK PHOTO, not an AI-generated image."
            )
            fallback_url = product.image_url if (product and product.image_url) else "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=800&auto=format&fit=crop"
            return (fallback_url, False)
        # Client errors (401, 402, 403, 404, etc.) are configuration issues, surface them
        raise
