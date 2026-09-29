import sys
from pathlib import Path
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
