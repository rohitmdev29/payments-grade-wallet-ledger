"""
Money helpers.

All amounts are stored as whole paise in BIGINT columns.
Never use FLOAT or DOUBLE for money — floating point loses precision.
"""


def rupees_to_paise(rupees: float) -> int:
    """Convert rupees to paise. Used only for seeding or display."""
    return int(round(rupees * 100))


def format_paise(paise: int) -> str:
    """Format paise as a rupee string, e.g. 50100 -> '501.00'."""
    sign = "-" if paise < 0 else ""
    paise = abs(paise)
    return f"{sign}{paise // 100}.{paise % 100:02d}"
