"""Create predictable demo data for local development."""

from calendar import monthrange
from datetime import date

from sqlalchemy import select

from backend.auth import get_password_hash
from backend.billing import bill_due_date, calculate_monthly_charges
from backend.database import SessionLocal, create_tables
from backend.models import Bill, Flat, GymLog, PointEntry, User


def seed_database() -> None:
    create_tables()
    with SessionLocal() as session:
        users = session.scalars(select(User)).all()
        if users:
            # Upgrade demo accounts created before password hashing was added.
            upgraded = False
            for user in users:
                if user.password_hash.startswith("dev-only:"):
                    user.password_hash = get_password_hash(user.password_hash.removeprefix("dev-only:"))
                    upgraded = True
            if upgraded:
                session.commit()
            print("Database already has users; seed data was left unchanged.")
            return

        flats: list[Flat] = []
        for number in range(1, 21):
            flat = Flat(
                flat_no=f"{'A' if number <= 10 else 'B'}-{((number - 1) % 10) + 1:02d}",
                block="A" if number <= 10 else "B",
                type="2BHK" if number % 2 else "3BHK",
                area_sqft=950 + (number % 5) * 150,
            )
            flats.append(flat)
            session.add(flat)
        session.flush()

        session.add(User(name="Society Admin", email="admin@doom.com", password_hash=get_password_hash("admin123"), role="admin", flat_id=None))
        for index, flat in enumerate(flats, start=1):
            session.add(User(name=f"Resident {index:02d}", email=f"resident{index:02d}@doom.com", password_hash=get_password_hash("resident123"), role="resident", flat_id=flat.id))

        today = date.today()
        for months_ago in range(5, -1, -1):
            absolute_month = today.year * 12 + today.month - 1 - months_ago
            year, month = divmod(absolute_month, 12)
            month += 1
            days = monthrange(year, month)[1]
            due_date = bill_due_date(year, month)
            for index, flat in enumerate(flats, start=1):
                electric = 100 + ((index * 37 + month * 11) % 180)
                water = 10 + ((index * 7 + month * 3) % 35)
                visits = (index + month) % 9
                charges = calculate_monthly_charges(
                    units_electricity=electric,
                    units_water=water,
                    area_sqft=flat.area_sqft,
                    clubhouse_bookings=index % 3,
                    clubhouse_fee_per_booking=150,
                    gym_visits=visits,
                )
                for category, amount in charges.items():
                    if category == "total":
                        continue
                    units = electric if category == "electricity" else water if category == "water" else None
                    paid = (index + month) % 4 == 0
                    session.add(Bill(flat_id=flat.id, month=month, year=year, category=category, amount=amount, units=units, status="paid" if paid else "pending", due_date=due_date))
                for category, cap in (("cleanliness", 40), ("discipline", 30), ("events", 30)):
                    score = min(cap, max(0, cap - ((index * 3 + month * 2 + len(category)) % (cap // 2 + 1))))
                    session.add(PointEntry(flat_id=flat.id, month=month, year=year, category=category, points=score, note="Seeded monthly score"))
                for visit in range(visits):
                    day = min(days, 2 + visit * 3)
                    session.add(GymLog(flat_id=flat.id, date=date(year, month, day), minutes=30 + (visit % 3) * 15))
        session.commit()
        print("Seeded 20 flats, 21 users, and six months of demo activity.")


if __name__ == "__main__":
    seed_database()
