import re
from datetime import date
from typing import List

from app.schemas.campaign import ValidationResult
from app.schemas.product import FactSheet

BANNED_CLAIMS = ["free", "half price", "buy one get one", "guaranteed", "best in city"]


def validate_caption(
    caption: str,
    fact_sheet: FactSheet,
    today: date,
) -> ValidationResult:
    """
    Validates a rendered caption against the database FactSheet truth on `today`.
    Returns ValidationResult containing pass/fail status and a list of issues.
    Issue codes used: OUT_OF_STOCK, OFFER_EXPIRED, BANNED_CLAIM, PRICE_MISMATCH, UNKNOWN_NUMBER.
    No LLM used.
    """
    issues: List[str] = []

    # 1. OUT_OF_STOCK check
    if fact_sheet.stock_qty <= 0:
        issues.append("OUT_OF_STOCK: Product is out of stock.")

    # 2. OFFER_EXPIRED check
    if fact_sheet.offer_valid_to:
        try:
            valid_to_dt = date.fromisoformat(fact_sheet.offer_valid_to)
            if valid_to_dt < today:
                issues.append(
                    f"OFFER_EXPIRED: Offer valid until {fact_sheet.offer_valid_to}, but today is {today.isoformat()}."
                )
        except ValueError:
            pass

    # 3. BANNED_CLAIM check
    caption_lower = caption.lower()
    for phrase in BANNED_CLAIMS:
        if phrase in caption_lower:
            issues.append(f"BANNED_CLAIM: Caption contains prohibited claim '{phrase}'.")

    # 4. Number validation against FactSheet
    fact_numbers: List[float] = []
    if fact_sheet.price is not None:
        fact_numbers.append(float(fact_sheet.price))
    if fact_sheet.offer_price is not None:
        fact_numbers.append(float(fact_sheet.offer_price))
    if fact_sheet.discount_percent is not None:
        fact_numbers.append(float(fact_sheet.discount_percent))

    if fact_sheet.offer_valid_to:
        for p in fact_sheet.offer_valid_to.split("-"):
            if p.isdigit():
                fact_numbers.append(float(int(p)))

    name_nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", fact_sheet.product_name)]
    biz_nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", fact_sheet.business_name)]

    caption_matches = list(re.finditer(r"\d+(?:\.\d+)?", caption))

    allowed_name_nums = list(name_nums + biz_nums)
    allowed_fact_nums = list(fact_numbers)

    for m in caption_matches:
        num_str = m.group(0)
        val = float(num_str)

        if val in allowed_name_nums:
            allowed_name_nums.remove(val)
            continue

        if val in allowed_fact_nums:
            continue

        start, end = m.span()
        window_start = max(0, start - 20)
        window_end = min(len(caption), end + 20)
        window_text = caption[window_start:window_end].lower()

        if re.search(r"%\s*off|off\b|discount|\binr\b|\brs\b|₹|price|cost|val", window_text):
            issues.append(
                f"PRICE_MISMATCH: Number {num_str} in caption does not match FactSheet values."
            )
        else:
            issues.append(
                f"UNKNOWN_NUMBER: Caption contains extra/unverified number {num_str} not in FactSheet."
            )

    passed = len(issues) == 0
    return ValidationResult(passed=passed, issues=issues)
