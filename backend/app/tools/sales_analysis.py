from datetime import date, timedelta
from typing import List, Optional
import pandas as pd

from app.schemas.business import ProductSalesStat, SalesRecord, SalesSummary
from app.schemas.product import Product


def analyze_sales(
    sales: List[SalesRecord],
    products: List[Product],
    today: date,
    period_days: int = 30,
    business_id: str = "biz_101",
) -> SalesSummary:
    """
    Analyzes sales records for the given products over the period ending on today.
    Uses pandas for deterministic calculations.
    """
    start_date = today - timedelta(days=period_days)

    if sales:
        raw_data = [s.model_dump() for s in sales]
        df = pd.DataFrame(raw_data)
        df["dt"] = pd.to_datetime(df["date"]).dt.date
        filtered_df = df[(df["dt"] >= start_date) & (df["dt"] <= today)].copy()
    else:
        filtered_df = pd.DataFrame()

    product_stats: List[ProductSalesStat] = []

    for product in products:
        p_id = product.product_id
        if not filtered_df.empty:
            p_df = filtered_df[filtered_df["product_id"] == p_id]
        else:
            p_df = pd.DataFrame()

        if not p_df.empty:
            units_sold = int(p_df["quantity"].sum())
            revenue = float((p_df["quantity"] * p_df["unit_price"]).sum())
            cust_counts = p_df.groupby("customer_id")["order_id"].count()
            repeat_customers = int((cust_counts >= 2).sum())
        else:
            units_sold = 0
            revenue = 0.0
            repeat_customers = 0

        stock_qty = product.stock_qty

        if units_sold > 0:
            daily_sales_rate = units_sold / float(period_days)
            days_of_stock_left = round(stock_qty / daily_sales_rate, 1)
        else:
            days_of_stock_left = 999.0 if stock_qty > 0 else 0.0

        product_stats.append(
            ProductSalesStat(
                product_id=p_id,
                units_sold=units_sold,
                revenue=revenue,
                stock_qty=stock_qty,
                days_of_stock_left=days_of_stock_left,
                repeat_customers=repeat_customers,
            )
        )

    total_revenue = float(sum(stat.revenue for stat in product_stats))

    if not filtered_df.empty:
        total_orders = int(filtered_df["order_id"].nunique())
    else:
        total_orders = 0

    top_product = max(product_stats, key=lambda s: s.revenue) if product_stats else None
    top_selling_product_id = (
        top_product.product_id if top_product and top_product.revenue > 0 else (products[0].product_id if products else None)
    )

    return SalesSummary(
        business_id=business_id,
        period_days=period_days,
        total_revenue=total_revenue,
        total_orders=total_orders,
        top_selling_product_id=top_selling_product_id,
        product_stats=product_stats,
    )
