import sys
from datetime import date
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agents.decision_agent import decide_product
from app.schemas.business import ProductSalesStat, SalesSummary
from app.schemas.campaign import DecisionResult
from app.schemas.product import Offer, Product

FIXED_TODAY = date(2026, 9, 28)


@pytest.fixture
def decision_fixture_data():
    products = [
        Product(product_id="prod_001", name="Chocolate Truffle Cake", category="Cakes", price=450.0, stock_qty=12),
        Product(product_id="prod_002", name="Whole Wheat Cookies", category="Cookies", price=120.0, stock_qty=60),
    ]
    offers = [
        Offer(offer_id="off_01", product_id="prod_001", discount_percent=15.0, valid_from=date(2026, 9, 20), valid_to=date(2026, 10, 10), active=True),
    ]
    sales_summary = SalesSummary(
        business_id="biz_101",
        period_days=30,
        total_revenue=15000.0,
        total_orders=35,
        top_selling_product_id="prod_001",
        product_stats=[
            ProductSalesStat(product_id="prod_001", units_sold=30, revenue=13500.0, stock_qty=12, days_of_stock_left=12.0, repeat_customers=5),
            ProductSalesStat(product_id="prod_002", units_sold=12, revenue=1440.0, stock_qty=60, days_of_stock_left=150.0, repeat_customers=2),
        ],
    )
    return sales_summary, products, offers


def test_decide_product_good_response(decision_fixture_data):
    sales_summary, products, offers = decision_fixture_data
    good_mock = DecisionResult(
        product_id="prod_001",
        reason="Top selling product with active discount offer",
        strategy="boost_bestseller",
        offer_id="off_01",
    )

    result = decide_product(
        sales_summary,
        products,
        goal="Boost weekend cake sales",
        today=FIXED_TODAY,
        offers=offers,
        llm_mock_responses=[good_mock],
    )

    assert result.product_id == "prod_001"
    assert result.strategy == "boost_bestseller"
    assert result.offer_id == "off_01"


def test_decide_product_nonexistent_offer_id_retries(decision_fixture_data):
    sales_summary, products, offers = decision_fixture_data
    bad_mock = DecisionResult(
        product_id="prod_001",
        reason="Selected cake with fake offer",
        strategy="boost_bestseller",
        offer_id="off_999",
    )
    corrected_mock = DecisionResult(
        product_id="prod_001",
        reason="Selected cake with valid offer after retry",
        strategy="boost_bestseller",
        offer_id="off_01",
    )

    result = decide_product(
        sales_summary,
        products,
        goal="Boost sales",
        today=FIXED_TODAY,
        offers=offers,
        llm_mock_responses=[bad_mock, corrected_mock],
    )

    assert result.product_id == "prod_001"
    assert result.offer_id == "off_01"


def test_decide_product_invalid_retries_fail(decision_fixture_data):
    sales_summary, products, offers = decision_fixture_data
    bad_mock = DecisionResult(
        product_id="prod_999",
        reason="Selected non-existent product",
        strategy="boost_bestseller",
        offer_id=None,
    )

    with pytest.raises(ValueError) as exc_info:
        decide_product(
            sales_summary,
            products,
            goal="Boost sales",
            today=FIXED_TODAY,
            offers=offers,
            llm_mock_responses=[bad_mock, bad_mock],
        )

    assert "Decision agent failed after 1 retry" in str(exc_info.value)
