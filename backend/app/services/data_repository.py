import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config.settings import settings
from app.schemas.business import BusinessProfile, SalesRecord
from app.schemas.product import Offer, Product
from app.services.supabase_client import get_client

logger = logging.getLogger(__name__)

# Base directories for sample data and local session data
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLE_DATA_DIR = PROJECT_ROOT / "data"

# Ensure backend/data directory exists for local persistence
LOCAL_DATA_DIR = BACKEND_DIR / "data"
LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

LOCAL_CAMPAIGNS_FILE = LOCAL_DATA_DIR / "local_campaigns.json"
LOCAL_ACTIVITY_LOG_FILE = LOCAL_DATA_DIR / "local_activity_log.json"


def _read_json_file(file_path: Path) -> Any:
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json_file(file_path: Path, data: Any) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def get_business(business_id: str) -> BusinessProfile:
    """Retrieves business profile for the given business_id."""
    if settings.use_sample_data:
        data = _read_json_file(SAMPLE_DATA_DIR / "sample_business.json")
        if data:
            profile = BusinessProfile(**data)
            if profile.business_id == business_id:
                return profile
            raise ValueError(f"Business profile '{business_id}' not found in sample data")
        raise ValueError(f"Sample business profile not found in {SAMPLE_DATA_DIR}")

    client = get_client()
    response = client.table("businesses").select("*").eq("business_id", business_id).single().execute()
    if not response.data:
        raise ValueError(f"Business profile '{business_id}' not found in Supabase")
    return BusinessProfile(**response.data)


def get_products(business_id: str) -> List[Product]:
    """Retrieves list of products for the given business_id."""
    if settings.use_sample_data:
        raw_list = _read_json_file(SAMPLE_DATA_DIR / "sample_products.json") or []
        products = [Product(**item) for item in raw_list]
        return products

    client = get_client()
    response = client.table("products").select("*").eq("business_id", business_id).execute()
    return [Product(**item) for item in (response.data or [])]


def get_offers(product_ids: List[str]) -> List[Offer]:
    """Retrieves list of offers for the given product_ids."""
    if settings.use_sample_data:
        raw_list = _read_json_file(SAMPLE_DATA_DIR / "sample_offers.json") or []
        offers = [Offer(**item) for item in raw_list]
        target_set = set(product_ids)
        return [o for o in offers if o.product_id in target_set]

    client = get_client()
    response = client.table("offers").select("*").in_("product_id", product_ids).execute()
    return [Offer(**item) for item in (response.data or [])]


def get_sales_records(business_id: str, since_date: date) -> List[SalesRecord]:
    """Retrieves list of sales records for a business starting from since_date."""
    if settings.use_sample_data:
        raw_list = _read_json_file(SAMPLE_DATA_DIR / "sample_sales.json") or []
        records = [SalesRecord(**item) for item in raw_list]
        filtered = [
            r for r in records
            if date.fromisoformat(r.date) >= since_date
        ]
        return filtered

    client = get_client()
    response = (
        client.table("sales_records")
        .select("*")
        .eq("business_id", business_id)
        .gte("date", since_date.isoformat())
        .execute()
    )
    return [SalesRecord(**item) for item in (response.data or [])]


def get_campaign(campaign_id: str) -> Optional[dict]:
    """Retrieves campaign state dict by campaign_id."""
    if settings.use_sample_data:
        campaigns_dict = _read_json_file(LOCAL_CAMPAIGNS_FILE) or {}
        if campaign_id in campaigns_dict:
            return campaigns_dict[campaign_id]
        
        # Check sample campaigns file if present
        sample_campaigns = _read_json_file(SAMPLE_DATA_DIR / "sample_campaigns.json") or []
        for camp in sample_campaigns:
            if isinstance(camp, dict) and camp.get("campaign_id") == campaign_id:
                return camp
        return None

    client = get_client()
    response = client.table("campaigns").select("state").eq("campaign_id", campaign_id).execute()
    if response.data and len(response.data) > 0:
        row = response.data[0]
        return row.get("state") or row
    return None


def save_campaign(campaign_id: str, state: dict) -> None:
    """Saves/upserts campaign state dict."""
    if settings.use_sample_data:
        campaigns_dict = _read_json_file(LOCAL_CAMPAIGNS_FILE) or {}
        campaigns_dict[campaign_id] = state
        _write_json_file(LOCAL_CAMPAIGNS_FILE, campaigns_dict)
        return

    client = get_client()
    client.table("campaigns").upsert({"campaign_id": campaign_id, "state": state}).execute()


def append_activity_log(campaign_id: str, event: str, detail: dict) -> None:
    """Appends an activity log entry for a campaign."""
    if settings.use_sample_data:
        logs_list = _read_json_file(LOCAL_ACTIVITY_LOG_FILE) or []
        entry = {
            "campaign_id": campaign_id,
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "detail": detail,
        }
        logs_list.append(entry)
        _write_json_file(LOCAL_ACTIVITY_LOG_FILE, logs_list)
        return

    client = get_client()
    client.table("activity_logs").insert({
        "campaign_id": campaign_id,
        "event": event,
        "detail": detail,
    }).execute()


def get_activity_log(campaign_id: str) -> List[dict]:
    """Retrieves ordered list of activity log entries for a campaign."""
    if settings.use_sample_data:
        logs_list = _read_json_file(LOCAL_ACTIVITY_LOG_FILE) or []
        filtered = [item for item in logs_list if item.get("campaign_id") == campaign_id]
        return filtered

    client = get_client()
    response = (
        client.table("activity_logs")
        .select("*")
        .eq("campaign_id", campaign_id)
        .order("timestamp", desc=False)
        .execute()
    )
    return response.data or []
