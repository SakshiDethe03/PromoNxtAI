import string
from app.schemas.product import FactSheet


def render_caption(template: str, fact_sheet: FactSheet) -> str:
    """
    Renders a caption template using values from FactSheet.
    Fails with ValueError if a required placeholder cannot be filled by the FactSheet.
    """
    formatter = string.Formatter()
    placeholders_in_template = set()
    for _, field_name, _, _ in formatter.parse(template):
        if field_name is not None:
            clean_field = field_name.split("!")[0].split(":")[0].strip()
            placeholders_in_template.add(clean_field)

    values = {}

    if "price" in placeholders_in_template:
        p = fact_sheet.price
        values["price"] = int(p) if p.is_integer() else p

    if "offer_price" in placeholders_in_template:
        if fact_sheet.offer_price is None:
            raise ValueError("Template requires {offer_price} but FactSheet has no active offer.")
        op = fact_sheet.offer_price
        values["offer_price"] = int(op) if op.is_integer() else op

    if "discount" in placeholders_in_template:
        if fact_sheet.discount_percent is None:
            raise ValueError("Template requires {discount} but FactSheet has no active offer discount.")
        disc = fact_sheet.discount_percent
        disc_val = int(disc) if disc.is_integer() else disc
        if "{discount}%" in template:
            values["discount"] = str(disc_val)
        else:
            values["discount"] = f"{disc_val}%"

    if "valid_to" in placeholders_in_template:
        if fact_sheet.offer_valid_to is None:
            raise ValueError("Template requires {valid_to} but FactSheet has no active offer validity date.")
        values["valid_to"] = fact_sheet.offer_valid_to

    try:
        return template.format(**values)
    except KeyError as e:
        raise ValueError(f"Template uses placeholder {e} which is not supported or missing in FactSheet.")
