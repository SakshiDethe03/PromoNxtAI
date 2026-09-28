from typing import List, Optional
from pydantic import BaseModel, Field


class BusinessProfile(BaseModel):
    """Business profile aligned with data/sample_business.json."""
    business_id: str
    name: str
    business_type: str
    city: str
    languages: List[str] = Field(default_factory=list)
    brand_voice: str
    instagram_handle: Optional[str] = None
    description: str


class SalesRecord(BaseModel):
    """Individual sales order record aligned with data/sample_sales.json."""
    order_id: str
    date: str
    customer_id: str
    product_id: str
    quantity: int
    unit_price: float


class ProductSalesStat(BaseModel):
    """Product-level sales metrics over the aggregation period."""
    product_id: str
    units_sold: int
    revenue: float
    stock_qty: int
    days_of_stock_left: float
    repeat_customers: int


class SalesSummary(BaseModel):
    """Aggregated sales data for the last 30 days used in decision making."""
    business_id: str
    period_days: int = 30
    total_revenue: float
    total_orders: int
    top_selling_product_id: Optional[str] = None
    product_stats: List[ProductSalesStat] = Field(default_factory=list)
