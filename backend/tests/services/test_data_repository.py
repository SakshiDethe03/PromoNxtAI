import json
import sys
from datetime import date
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config.settings import settings
from app.schemas.business import BusinessProfile, SalesRecord
from app.schemas.product import Offer, Product
from app.services.data_repository import (
    LOCAL_ACTIVITY_LOG_FILE,
    LOCAL_CAMPAIGNS_FILE,
    append_activity_log,
    get_business,
    get_campaign,
    get_offers,
    get_products,
    get_sales_records,
    save_campaign,
)


@pytest.fixture(autouse=True)
def setup_sample_data_mode():
    settings.use_sample_data = True


def test_get_business_sample_data():
    biz = get_business("biz_101")
    assert isinstance(biz, BusinessProfile)
    assert biz.business_id == "biz_101"
    assert biz.name == "Sharma Bakery & Sweets"


def test_get_products_sample_data():
    products = get_products("biz_101")
    assert isinstance(products, list)
    assert len(products) == 4
    assert all(isinstance(p, Product) for p in products)
    assert any(p.product_id == "prod_001" for p in products)


def test_get_offers_sample_data():
    offers = get_offers(["prod_001", "prod_002"])
    assert isinstance(offers, list)
    assert len(offers) == 2
    assert all(isinstance(o, Offer) for o in offers)
    assert any(o.offer_id == "off_01" for o in offers)


def test_get_sales_records_sample_data():
    since = date(2026, 9, 20)
    sales = get_sales_records("biz_101", since)
    assert isinstance(sales, list)
    assert len(sales) > 0
    assert all(isinstance(s, SalesRecord) for s in sales)
    assert all(date.fromisoformat(s.date) >= since for s in sales)


def test_save_and_get_campaign_local_json():
    camp_id = "camp_test_999"
    test_state = {
        "campaign_id": camp_id,
        "business_id": "biz_101",
        "status": "draft",
        "input": "Promote festive laddoo",
    }

    save_campaign(camp_id, test_state)

    retrieved = get_campaign(camp_id)
    assert retrieved is not None
    assert retrieved["campaign_id"] == camp_id
    assert retrieved["status"] == "draft"


def test_append_activity_log_local_json():
    camp_id = "camp_test_999"
    event_name = "test_node_executed"
    detail_data = {"status": "success", "attempt": 1}

    append_activity_log(camp_id, event_name, detail_data)

    assert LOCAL_ACTIVITY_LOG_FILE.exists()
    with open(LOCAL_ACTIVITY_LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    assert isinstance(logs, list)
    assert any(
        log["campaign_id"] == camp_id and log["event"] == event_name and log["detail"] == detail_data
        for log in logs
    )
