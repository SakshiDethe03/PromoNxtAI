from datetime import date
from typing import List, Optional

from app.schemas.business import BusinessProfile
from app.schemas.product import FactSheet, Offer, Product


def build_fact_sheet(
    business: BusinessProfile,
    product: Product,
    offers: List[Offer],
    today: date,
) -> FactSheet:
    """
    Builds a FactSheet for a product, selecting an active valid offer on `today`
    and calculating offer_price in code.
    Raises ValueError if product is out of stock.
    """
    if product.stock_qty <= 0:
        raise ValueError(
            f"Product '{product.name}' (ID: {product.product_id}) is out of stock (stock_qty={product.stock_qty})."
        )

    valid_offer: Optional[Offer] = None
    for offer in offers:
        if offer.product_id == product.product_id and offer.is_valid_on(today):
            valid_offer = offer
            break

    if valid_offer is not None:
        discount_percent = valid_offer.discount_percent
        offer_price = round(product.price * (1.0 - discount_percent / 100.0), 2)
        offer_valid_to = valid_offer.valid_to.isoformat()
    else:
        discount_percent = None
        offer_price = None
        offer_valid_to = None

    return FactSheet(
        business_name=business.name,
        product_id=product.product_id,
        product_name=product.name,
        price=product.price,
        currency=product.currency,
        stock_qty=product.stock_qty,
        discount_percent=discount_percent,
        offer_price=offer_price,
        offer_valid_to=offer_valid_to,
    )
