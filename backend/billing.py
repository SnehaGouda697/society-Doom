"""Small, deterministic billing calculations used when creating monthly bills."""

from datetime import date

# All fees are kept together so an administrator can adjust them easily.
RATES = {
    "electricity_per_unit": 8.0,
    "water_per_unit": 2.0,
    "maintenance_per_sqft": 2.5,
    "clubhouse_base_fee": 300.0,
    "gym_per_visit": 50.0,
}

CATEGORIES = ("electricity", "water", "maintenance", "clubhouse", "gym")


def _non_negative(value: float, name: str) -> float:
    value = float(value)
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return value


def electricity_bill(units: float, rate: float | None = None) -> float:
    return round(_non_negative(units, "units") * (RATES["electricity_per_unit"] if rate is None else _non_negative(rate, "rate")), 2)


def water_bill(units: float, rate: float | None = None) -> float:
    return round(_non_negative(units, "units") * (RATES["water_per_unit"] if rate is None else _non_negative(rate, "rate")), 2)


def maintenance_bill(area_sqft: float, rate: float | None = None) -> float:
    return round(_non_negative(area_sqft, "area") * (RATES["maintenance_per_sqft"] if rate is None else _non_negative(rate, "rate")), 2)


def clubhouse_bill(bookings: int = 0, fee_per_booking: float = 0.0, base_fee: float | None = None) -> float:
    if int(bookings) < 0:
        raise ValueError("bookings cannot be negative")
    base = RATES["clubhouse_base_fee"] if base_fee is None else _non_negative(base_fee, "base fee")
    return round(base + int(bookings) * _non_negative(fee_per_booking, "booking fee"), 2)


def gym_bill(visits: int, fee_per_visit: float | None = None) -> float:
    if int(visits) < 0:
        raise ValueError("visits cannot be negative")
    rate = RATES["gym_per_visit"] if fee_per_visit is None else _non_negative(fee_per_visit, "visit fee")
    return round(int(visits) * rate, 2)


def calculate_monthly_charges(*, units_electricity: float, units_water: float, area_sqft: float, clubhouse_bookings: int = 0, gym_visits: int = 0, clubhouse_fee_per_booking: float = 0.0) -> dict[str, float]:
    """Return each bill category and the total for one flat."""
    charges = {
        "electricity": electricity_bill(units_electricity),
        "water": water_bill(units_water),
        "maintenance": maintenance_bill(area_sqft),
        "clubhouse": clubhouse_bill(clubhouse_bookings, clubhouse_fee_per_booking),
        "gym": gym_bill(gym_visits),
    }
    charges["total"] = round(sum(charges.values()), 2)
    return charges


def bill_due_date(year: int, month: int) -> date:
    """Monthly bills are due on the 15th of the following month."""
    if not 1 <= month <= 12:
        raise ValueError("month must be between 1 and 12")
    if month == 12:
        return date(year + 1, 1, 15)
    return date(year, month + 1, 15)
