import sys
from datetime import date
from pathlib import Path
import pytest
from pydantic import ValidationError

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agents.content_agent import generate_content
from app.schemas.business import BusinessProfile
from app.schemas.campaign import GeneratedContent
from app.schemas.product import FactSheet


@pytest.fixture
def content_fixture_data():
    business = BusinessProfile(
        business_id="biz_101",
        name="Sharma Bakery & Sweets",
        business_type="bakery",
        city="Nagpur",
        languages=["English", "Hindi"],
        brand_voice="Warm, friendly, local",
        description="Neighbourhood bakery",
    )
    fact_sheet = FactSheet(
        business_name="Sharma Bakery & Sweets",
        product_id="prod_001",
        product_name="Chocolate Truffle Cake (500g)",
        price=450.0,
        currency="INR",
        stock_qty=12,
        discount_percent=15.0,
        offer_price=382.5,
        offer_valid_to="2026-10-10",
    )
    return business, fact_sheet


def test_generate_content_good_response(content_fixture_data):
    business, fact_sheet = content_fixture_data
    good_mock = GeneratedContent(
        caption_template="Treat yourself! Special offer at {offer_price} INR (get {discount} off) valid until {valid_to}.",
        cta="Order on WhatsApp now",
        hashtags=["#FreshCakes"],
        creative_brief="Cake visual",
    )

    result = generate_content(
        fact_sheet,
        business,
        language="English",
        goal="Boost sales",
        llm_mock_responses=[good_mock],
    )

    assert result.caption_template.startswith("Treat yourself!")
    assert "{offer_price}" in result.caption_template
    assert result.cta == "Order on WhatsApp now"


def test_generate_content_raw_digits_retries_and_succeeds(content_fixture_data):
    business, fact_sheet = content_fixture_data
    bad_dict = {
        "caption_template": "Get 20% off on cakes today!",
        "cta": "Order now",
        "hashtags": ["#Cakes"],
        "creative_brief": "Cake visual",
    }
    corrected_mock = GeneratedContent(
        caption_template="Treat yourself! Special offer at {offer_price} INR! Valid until {valid_to}.",
        cta="Order on WhatsApp now",
        hashtags=["#Cakes"],
        creative_brief="Cake visual",
    )

    result = generate_content(
        fact_sheet,
        business,
        language="English",
        goal="Boost sales",
        llm_mock_responses=[bad_dict, corrected_mock],
    )

    assert "{offer_price}" in result.caption_template


def test_generate_content_persistent_raw_digits_fails(content_fixture_data):
    business, fact_sheet = content_fixture_data
    bad_dict = {
        "caption_template": "Get 20% off on cakes today!",
        "cta": "Order now",
        "hashtags": ["#Cakes"],
        "creative_brief": "Cake visual",
    }

    with pytest.raises(ValidationError) as exc_info:
        generate_content(
            fact_sheet,
            business,
            language="English",
            goal="Boost sales",
            llm_mock_responses=[bad_dict, bad_dict],
        )

    assert "must not contain raw digits" in str(exc_info.value)
