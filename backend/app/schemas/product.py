from datetime import date
from typing import Optional, Union
from pydantic import BaseModel, Field, model_validator


class Offer(BaseModel):
    """Offer model for product discounts."""
    offer_id: str
    product_id: str
    discount_percent: float
    valid_from: date
    valid_to: date
    active: bool = True

    @model_validator(mode="after")
    def validate_dates(self) -> "Offer":
        if self.valid_from > self.valid_to:
            raise ValueError(f"valid_from ({self.valid_from}) must be <= valid_to ({self.valid_to})")
        return self

    def is_valid_on(self, today: Union[date, str]) -> bool:
        """Check if offer is active and valid on a given date."""
        if not self.active:
            return False
        if isinstance(today, str):
            today = date.fromisoformat(today)
        return self.valid_from <= today <= self.valid_to


class Product(BaseModel):
    """Product model aligned with data/sample_products.json."""
    product_id: str
    name: str
    category: str
    price: float
    currency: str = "INR"
    stock_qty: int = 0
    is_seasonal: bool = False
    image_url: Optional[str] = None


class FactSheet(BaseModel):
    """Single source of truth for factual validation. Code injects facts here."""
    business_name: str
    product_id: str
    product_name: str
    price: float
    currency: str = "INR"
    stock_qty: int = 0
    discount_percent: Optional[float] = None
    offer_price: Optional[float] = None
    offer_valid_to: Optional[str] = None
