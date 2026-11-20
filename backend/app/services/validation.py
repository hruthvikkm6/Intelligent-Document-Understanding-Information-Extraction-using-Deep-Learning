from datetime import date


def validate_fields(fields: dict, threshold: float) -> dict:
    issues: list[str] = []
    for key in ("invoice_date", "due_date"):
        value = fields.get(key, {}).get("value")
        if value:
            try:
                date.fromisoformat(value)
            except (TypeError, ValueError):
                issues.append(f"{key.replace('_', ' ').title()} is not a valid date")
    for key in ("subtotal", "tax", "total"):
        value = fields.get(key, {}).get("value")
        if value is not None and (not isinstance(value, (int, float)) or value < 0):
            issues.append(f"{key.title()} must be a non-negative number")
    for key, field in fields.items():
        confidence = field.get("confidence") if isinstance(field, dict) else None
        if (
            isinstance(field, dict)
            and field.get("value") is not None
            and confidence is not None
            and confidence < threshold
        ):
            issues.append(
                f"{key.replace('_', ' ').title()} confidence is below the {threshold:.0%} threshold"
            )
    for key, label in (
        ("vendor_name", "Vendor name"),
        ("invoice_number", "Invoice number"),
        ("invoice_date", "Invoice date"),
        ("total", "Total amount"),
    ):
        if fields.get(key, {}).get("value") in (None, ""):
            issues.append(f"{label} was not identified")
    if fields.get("currency", {}).get("value") in (None, "UNKNOWN"):
        issues.append("Currency was not identified")
    elif fields["currency"]["value"] not in {
        "INR",
        "USD",
        "EUR",
        "GBP",
        "JPY",
        "CAD",
        "AUD",
        "CNY",
        "SGD",
        "AED",
        "CHF",
    }:
        issues.append("Currency code is not recognized")
    subtotal, tax, total = (fields.get(k, {}).get("value") for k in ("subtotal", "tax", "total"))
    if all(isinstance(v, (int, float)) for v in (subtotal, tax, total)) and abs(
        subtotal + tax - total
    ) > max(0.02, total * 0.02):
        issues.append("Subtotal plus tax differs from total by more than 2%")
    return {
        "status": "warning" if issues else "passed",
        "issues": issues,
        "confidence_threshold": threshold,
    }
