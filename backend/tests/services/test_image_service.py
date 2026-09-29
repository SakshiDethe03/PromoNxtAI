import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config.settings import settings
from app.schemas.business import BusinessProfile
from app.schemas.product import Product
from app.services.image_service import build_image_prompt, generate_poster_image


@pytest.fixture
def sample_product_and_business():
    product = Product(
        product_id="prod_001",
        name="Chocolate Truffle Cake (500g)",
        category="Cakes",
        price=450.0,
        currency="INR",
        stock_qty=12,
        image_url="https://example.com/truffle.jpg",
    )
    business = BusinessProfile(
        business_id="biz_101",
        name="Sharma Bakery & Sweets",
        business_type="bakery",
        city="Nagpur",
        brand_voice="Warm, friendly, local",
        description="Neighbourhood bakery",
    )
    return product, business


def test_image_prompt_never_contains_price_currency_or_digits_from_product(sample_product_and_business):
    product, business = sample_product_and_business

    prompt = build_image_prompt(product, business)

    assert product.category in prompt
    assert business.brand_voice in prompt

    assert str(product.price) not in prompt
    assert str(int(product.price)) not in prompt
    assert product.currency not in prompt

    prompt_upper = prompt.upper()
    assert "NO TEXT" in prompt_upper
    assert "NO NUMBERS" in prompt_upper
    assert "NO PRICES" in prompt_upper
    assert "NO DISCOUNT" in prompt_upper


def test_generate_poster_image_mock(sample_product_and_business):
    product, business = sample_product_and_business
    settings.image_mock = True

    url = generate_poster_image(product, business)
    assert url == product.image_url


@patch("app.services.image_service.create_client")
@patch("requests.post")
def test_generate_poster_image_openrouter_call(mock_post, mock_supabase, sample_product_and_business):
    product, business = sample_product_and_business
    settings.image_mock = False
    settings.use_sample_data = False

    mock_img_resp = MagicMock()
    mock_img_resp.status_code = 200
    mock_img_resp.json.return_value = {
        "data": [{"url": "https://openrouter.ai/generated_image.png"}]
    }
    mock_bytes_resp = MagicMock()
    mock_bytes_resp.status_code = 200
    mock_bytes_resp.content = b"fake_image_bytes"

    mock_post.side_effect = [mock_img_resp, mock_bytes_resp]

    mock_storage = MagicMock()
    mock_storage.get_public_url.return_value = "https://supabase.co/public_poster.png"
    mock_supabase_client = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_storage
    mock_supabase.return_value = mock_supabase_client

    url = generate_poster_image(product, business)

    assert url == "https://supabase.co/public_poster.png"
    first_call = mock_post.call_args_list[0]
    assert first_call[0][0] == "https://openrouter.ai/api/v1/images"
    assert first_call[1]["headers"]["Authorization"] == f"Bearer {settings.openrouter_api_key}"
    payload = first_call[1]["json"]
    assert payload["modalities"] == ["image"]
    assert payload["aspect_ratio"] == "1:1"
    assert payload["output_format"] == "jpeg"
