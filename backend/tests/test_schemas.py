import json
import sys
from datetime import date
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError

from app.schemas.business import BusinessProfile, SalesRecord, ProductSalesStat, SalesSummary
from app.schemas.campaign import (
    ApprovalDecision,
    DecisionResult,
    GeneratedContent,
    PublishCallback,
    PublishPayload,
    ValidationResult,
)
from app.schemas.product import FactSheet, Offer, Product
from app.graph.state import CampaignState


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def test_load_all_5_data_files():
    # 1. sample_business.json
    business_file = DATA_DIR / "sample_business.json"
    with open(business_file, "r") as f:
        business_data = json.load(f)
    profile = BusinessProfile(**business_data)
    assert profile.business_id == "biz_101"

    # 2. sample_products.json
    products_file = DATA_DIR / "sample_products.json"
    with open(products_file, "r") as f:
        products_data = json.load(f)
    products = [Product(**item) for item in products_data]
    assert len(products) == 4
    assert any(p.stock_qty == 0 for p in products)
    assert any(p.is_seasonal for p in products)

    # 3. sample_campaigns.json
    campaigns_file = DATA_DIR / "sample_campaigns.json"
    with open(campaigns_file, "r") as f:
        campaigns_data = json.load(f)
    assert len(campaigns_data) > 0

    # 4. sample_offers.json
    offers_file = DATA_DIR / "sample_offers.json"
    with open(offers_file, "r") as f:
        offers_data = json.load(f)
    offers = [Offer(**item) for item in offers_data]
    assert len(offers) == 2
    
    # Verify is_valid_on logic
    today = date(2026, 9, 28)
    active_offer = next(o for o in offers if o.offer_id == "off_01")
    expired_offer = next(o for o in offers if o.offer_id == "off_02")
    assert active_offer.is_valid_on(today) is True
    assert expired_offer.is_valid_on(today) is False

    # 5. sample_sales.json
    sales_file = DATA_DIR / "sample_sales.json"
    with open(sales_file, "r") as f:
        sales_data = json.load(f)
    sales = [SalesRecord(**item) for item in sales_data]
    assert len(sales) >= 40


def test_generated_content_digits_rejection():
    # Valid template with placeholders and NO raw digits
    valid = GeneratedContent(
        caption_template="Treat yourself to fresh treats! Special offer at {offer_price} INR! Valid until {valid_to}.",
        cta="Order on WhatsApp now!",
        hashtags=["#NagpurBakery", "#FreshCakes"],
        creative_brief="Delicious cake photo with warm lighting",
    )
    assert valid.caption_template.startswith("Treat yourself")

    # Invalid template containing raw digits (e.g. 20% or 450)
    try:
        GeneratedContent(
            caption_template="Get 20% off on cakes today!",
            cta="Order now!",
            hashtags=["#Cakes"],
            creative_brief="Cake photo",
        )
        assert False, "Should have raised ValidationError for raw digits"
    except ValidationError as e:
        assert "caption_template must not contain raw digits" in str(e)


def test_fact_sheet_and_decision():
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
    assert fact_sheet.offer_price == 382.5

    decision = DecisionResult(
        product_id="prod_001",
        reason="Top selling cake with active 15% discount",
        strategy="boost_bestseller",
        offer_id="off_01",
        target_segment="Cake lovers",
    )
    assert decision.strategy == "boost_bestseller"


def test_campaign_state():
    state: CampaignState = {
        "campaign_id": "camp_501",
        "business_id": "biz_101",
        "input": "Promote top seller",
        "language": "English",
        "goal": "Boost weekend sales",
        "final_caption": "Treat yourself to fresh cakes!",
        "image_url": "https://example.com/poster.png",
        "validation_attempts": 1,
        "status": "awaiting_approval",
        "errors": [],
    }
    assert state["status"] == "awaiting_approval"
    assert state["validation_attempts"] == 1


if __name__ == "__main__":
    test_load_all_5_data_files()
    test_generated_content_digits_rejection()
    test_fact_sheet_and_decision()
    test_campaign_state()
    print("ALL 5 DATA FILES LOADED & ALL SCHEMA TESTS PASSED SUCCESSFULLY!")
