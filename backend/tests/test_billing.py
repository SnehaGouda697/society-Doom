import pytest

from backend.billing import (
    bill_due_date,
    calculate_monthly_charges,
    clubhouse_bill,
    electricity_bill,
    gym_bill,
    maintenance_bill,
    water_bill,
)


def test_standard_bill_calculations():
    assert electricity_bill(100) == 800
    assert water_bill(10) == 20
    assert maintenance_bill(1000) == 2500
    assert clubhouse_bill(2, 100) == 500
    assert gym_bill(3) == 150


def test_monthly_total_matches_categories():
    charges = calculate_monthly_charges(
        units_electricity=100,
        units_water=10,
        area_sqft=1000,
        clubhouse_bookings=1,
        gym_visits=2,
        clubhouse_fee_per_booking=100,
    )
    assert charges == {"electricity": 800, "water": 20, "maintenance": 2500, "clubhouse": 400, "gym": 100, "total": 3820}


def test_invalid_inputs_and_year_boundary():
    with pytest.raises(ValueError):
        electricity_bill(-1)
    assert bill_due_date(2026, 12).isoformat() == "2027-01-15"
