import json
from datetime import date
from pathlib import Path
import pytest
from pydantic import ValidationError

from app.schemas.business import BusinessProfile, SalesRecord
from app.schemas.campaign import GeneratedContent
from app.schemas.product import FactSheet, Offer, Product

from app.tools.sales_analysis import analyze_sales
from app.tools.fact_sheet import build_fact_sheet
from app.tools.caption_renderer import render_caption
from app.tools.validators import validate_caption

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
FIXED_TODAY = date(2026, 9, 28)


@pytest.fixture
def sample_data():
    with open(DATA_DIR / "sample_business.json", "r") as f:
        business = BusinessProfile(**json.load(f))
    with open(DATA_DIR / "sample_products.json", "r") as f:
        products = [Product(**item) for item in json.load(f)]
    with open(DATA_DIR / "sample_offers.json", "r") as f:
        offers = [Offer(**item) for item in json.load(f)]
    with open(DATA_DIR / "sample_sales.json", "r") as f:
        sales = [SalesRecord(**item) for item in json.load(f)]
    return business, products, offers, sales


# --- SCHEMA HARDENING TESTS ---

def test_generated_content_cta_no_digits():
    # Valid: no digits in caption_template or cta
    valid = GeneratedContent(
        caption_template="Treat yourself! Special offer at {offer_price}! Valid to {valid_to}.",
        cta="Order on WhatsApp now",
        hashtags=["#Sweet"],
        creative_brief="Brief text",
    )
    assert valid.cta == "Order on WhatsApp now"

    # Invalid digits in CTA
    with pytest.raises(ValidationError) as exc_info:
        GeneratedContent(
            caption_template="Treat yourself at {offer_price}!",
            cta="Call us at 9876543210",
            hashtags=["#Sweet"],
            creative_brief="Brief text",
        )
    assert "must not contain raw digits" in str(exc_info.value)


def test_generated_content_invalid_placeholder():
    # Invalid placeholder {currency}
    with pytest.raises(ValidationError) as exc_info:
        GeneratedContent(
            caption_template="Get product for {price} {currency}!",
            cta="Order now",
            hashtags=[],
            creative_brief="Brief",
        )
    assert "Invalid placeholder '{currency}'" in str(exc_info.value)


def test_offer_valid_dates_validation():
    # Invalid offer: valid_from > valid_to
    with pytest.raises(ValidationError) as exc_info:
        Offer(
            offer_id="off_bad",
            product_id="prod_001",
            discount_percent=10.0,
            valid_from=date(2026, 10, 15),
            valid_to=date(2026, 10, 10),
            active=True,
        )
    assert "valid_from" in str(exc_info.value) and "must be <= valid_to" in str(exc_info.value)


# --- TOOL 1: SALES ANALYSIS TESTS ---

def test_sales_analysis_tool(sample_data):
    business, products, offers, sales = sample_data
    summary = analyze_sales(sales, products, FIXED_TODAY, period_days=30)
    assert summary.business_id == "biz_101"
    assert len(summary.product_stats) == 4
    assert summary.total_revenue > 0
    assert summary.total_orders > 0

    # Verify prod_004 exists in stats
    prod4_stat = next(s for s in summary.product_stats if s.product_id == "prod_004")
    assert prod4_stat.units_sold > 0
    assert prod4_stat.stock_qty == 45


# --- TOOL 2: FACT SHEET TESTS ---

def test_fact_sheet_tool_valid_offer(sample_data):
    business, products, offers, sales = sample_data
    prod1 = next(p for p in products if p.product_id == "prod_001")
    fact_sheet = build_fact_sheet(business, prod1, offers, FIXED_TODAY)

    assert fact_sheet.product_id == "prod_001"
    assert fact_sheet.price == 450.0
    assert fact_sheet.discount_percent == 15.0
    assert fact_sheet.offer_price == 382.5
    assert fact_sheet.offer_valid_to == "2026-10-10"


def test_fact_sheet_out_of_stock_raises_error(sample_data):
    business, products, offers, sales = sample_data
    prod3 = next(p for p in products if p.product_id == "prod_003")  # stock_qty == 0
    with pytest.raises(ValueError) as exc_info:
        build_fact_sheet(business, prod3, offers, FIXED_TODAY)
    assert "out of stock" in str(exc_info.value).lower()


# --- TOOL 3: CAPTION RENDERER TESTS ---

def test_caption_renderer_success(sample_data):
    business, products, offers, sales = sample_data
    prod1 = next(p for p in products if p.product_id == "prod_001")
    fact_sheet = build_fact_sheet(business, prod1, offers, FIXED_TODAY)
    template = "Treat yourself! Price is {price}, offer price is {offer_price} (get {discount} off) valid until {valid_to}."

    rendered = render_caption(template, fact_sheet)
    assert "Price is 450" in rendered
    assert "offer price is 382.5" in rendered
    assert "15% off" in rendered
    assert "2026-10-10" in rendered


def test_caption_renderer_missing_placeholder(sample_data):
    business, products, offers, sales = sample_data
    prod2 = next(p for p in products if p.product_id == "prod_002")  # offer off_02 expired by 2026-09-28
    fact_sheet = build_fact_sheet(business, prod2, offers, FIXED_TODAY)  # discount_percent will be None
    template = "Get special price at {offer_price}!"

    with pytest.raises(ValueError) as exc_info:
        render_caption(template, fact_sheet)
    assert "requires {offer_price}" in str(exc_info.value)


# --- TOOL 4: VALIDATION TESTS FOR REQUIRED SCENARIOS ---

def test_validate_caption_correct_passes(sample_data):
    business, products, offers, sales = sample_data
    prod1 = next(p for p in products if p.product_id == "prod_001")
    fact_sheet = build_fact_sheet(business, prod1, offers, FIXED_TODAY)
    caption = "Treat yourself to Chocolate Truffle Cake (500g)! Special offer at 382.5 INR (15% off) valid until 2026-10-10."

    res = validate_caption(caption, fact_sheet, FIXED_TODAY)
    assert res.passed is True
    assert len(res.issues) == 0


def test_validate_caption_wrong_price(sample_data):
    business, products, offers, sales = sample_data
    prod1 = next(p for p in products if p.product_id == "prod_001")
    fact_sheet = build_fact_sheet(business, prod1, offers, FIXED_TODAY)
    # Price 500 INR instead of 450 INR or offer_price 382.5
    caption = "Treat yourself to Chocolate Truffle Cake (500g)! Special offer at 500 INR valid until 2026-10-10."

    res = validate_caption(caption, fact_sheet, FIXED_TODAY)
    assert res.passed is False
    assert any("PRICE_MISMATCH" in issue or "UNKNOWN_NUMBER" in issue for issue in res.issues)


def test_validate_caption_invented_discount(sample_data):
    business, products, offers, sales = sample_data
    prod1 = next(p for p in products if p.product_id == "prod_001")
    fact_sheet = build_fact_sheet(business, prod1, offers, FIXED_TODAY)
    # 25% off instead of 15% off
    caption = "Treat yourself to Chocolate Truffle Cake (500g)! Special offer at 382.5 INR (25% off) valid until 2026-10-10."

    res = validate_caption(caption, fact_sheet, FIXED_TODAY)
    assert res.passed is False
    assert any("PRICE_MISMATCH" in issue for issue in res.issues)


def test_validate_caption_expired_offer(sample_data):
    business, products, offers, sales = sample_data
    prod1 = next(p for p in products if p.product_id == "prod_001")
    fact_sheet = build_fact_sheet(business, prod1, offers, FIXED_TODAY)
    # Manually set expired date in fact sheet
    fact_sheet.offer_valid_to = "2026-09-15"
    caption = "Treat yourself to Chocolate Truffle Cake (500g)! Special offer at 382.5 INR (15% off) valid until 2026-09-15."

    res = validate_caption(caption, fact_sheet, FIXED_TODAY)
    assert res.passed is False
    assert any("OFFER_EXPIRED" in issue for issue in res.issues)


def test_validate_caption_out_of_stock(sample_data):
    business, products, offers, sales = sample_data
    prod3 = next(p for p in products if p.product_id == "prod_003")
    # Force creation of fact_sheet with stock_qty = 0
    fact_sheet = FactSheet(
        business_name=business.name,
        product_id=prod3.product_id,
        product_name=prod3.name,
        price=prod3.price,
        currency=prod3.currency,
        stock_qty=0,
    )
    caption = "Enjoy fresh Kaju Katli Box (250g) today!"

    res = validate_caption(caption, fact_sheet, FIXED_TODAY)
    assert res.passed is False
    assert any("OUT_OF_STOCK" in issue for issue in res.issues)


def test_validate_caption_extra_number(sample_data):
    business, products, offers, sales = sample_data
    prod1 = next(p for p in products if p.product_id == "prod_001")
    fact_sheet = build_fact_sheet(business, prod1, offers, FIXED_TODAY)
    # Extra number 9876543210
    caption = "Treat yourself to Chocolate Truffle Cake (500g)! Special offer at 382.5 INR (15% off) valid until 2026-10-10. Call 9876543210!"

    res = validate_caption(caption, fact_sheet, FIXED_TODAY)
    assert res.passed is False
    assert any("UNKNOWN_NUMBER" in issue for issue in res.issues)


def test_validate_caption_banned_phrase(sample_data):
    business, products, offers, sales = sample_data
    prod1 = next(p for p in products if p.product_id == "prod_001")
    fact_sheet = build_fact_sheet(business, prod1, offers, FIXED_TODAY)
    caption = "Treat yourself to Chocolate Truffle Cake (500g)! Guaranteed best in city with free delivery!"

    res = validate_caption(caption, fact_sheet, FIXED_TODAY)
    assert res.passed is False
    assert any("BANNED_CLAIM" in issue for issue in res.issues)
