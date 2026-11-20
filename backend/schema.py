"""Strawberry GraphQL queries and mutations for Society Doom."""

from calendar import monthrange
from datetime import date

import strawberry
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.billing import bill_due_date, calculate_monthly_charges
from backend.auth import authenticate_user, create_access_token
from backend.models import Bill, Flat, GymLog, MaintenanceRequest, MeterReading, PointEntry, User
from backend.scoring import CATEGORY_MAXIMUMS, monthly_score, society_average


@strawberry.type
class BillType:
    id: int
    category: str
    amount: float
    units: float | None
    status: str
    due_date: date


@strawberry.type
class FlatSummary:
    flat_id: int
    flat_no: str
    score: int
    badge: str


@strawberry.type
class PointBreakdown:
    cleanliness: int
    discipline: int
    events: int
    total: int


@strawberry.type
class FlatReport:
    flat_id: int
    flat_no: str
    month: int
    year: int
    score: int
    badge: str
    points: PointBreakdown
    bills: list[BillType]
    total_billed: float


@strawberry.type
class SocietyReport:
    month: int
    year: int
    average_score: float
    flat_count: int
    total_billed: float
    collected: float
    pending: float
    doom_zone_count: int


@strawberry.type
class UsagePoint:
    month: int
    year: int
    units: float


@strawberry.type
class UserType:
    id: int
    name: str
    email: str
    role: str
    flat_id: int | None


@strawberry.type
class PropertyType:
    id: int
    flat_no: str
    block: str
    type: str
    area_sqft: int
    resident_count: int
    score: int
    badge: str


@strawberry.type
class TenantType:
    id: int
    name: str
    email: str
    role: str
    flat_no: str | None


@strawberry.type
class FinanceBillType:
    id: int
    flat_no: str
    category: str
    amount: float
    status: str
    due_date: date


@strawberry.type
class MaintenanceType:
    id: int
    flat_id: int
    flat_no: str
    title: str
    category: str
    description: str
    status: str
    created_on: date


@strawberry.type
class ActionResult:
    success: bool
    message: str
    count: int = 0


@strawberry.type
class LoginResult:
    success: bool
    message: str
    access_token: str | None = None
    user: UserType | None = None


def _session(info: strawberry.Info) -> Session:
    """Read the request-scoped session, or create one for direct local use."""
    session = info.context.get("session")
    if session is None:
        raise ValueError("GraphQL request context is missing a database session")
    return session


def _require_user(info: strawberry.Info) -> User:
    user = info.context.get("current_user")
    if user is None:
        raise ValueError("Authentication required. Log in before accessing this data.")
    return user


def _require_admin(info: strawberry.Info) -> User:
    user = _require_user(info)
    if user.role != "admin":
        raise ValueError("Admin access required for this action.")
    return user


def _report(session: Session, flat: Flat, month: int, year: int) -> FlatReport:
    score_data = monthly_score(session, flat.id, month, year)
    bills = session.scalars(
        select(Bill).where(Bill.flat_id == flat.id, Bill.month == month, Bill.year == year)
    ).all()
    point_values = PointBreakdown(
        cleanliness=int(score_data["cleanliness"]),
        discipline=int(score_data["discipline"]),
        events=int(score_data["events"]),
        total=int(score_data["total"]),
    )
    return FlatReport(
        flat_id=flat.id,
        flat_no=flat.flat_no,
        month=month,
        year=year,
        score=int(score_data["total"]),
        badge=str(score_data["badge"]),
        points=point_values,
        bills=[BillType(id=b.id, category=b.category, amount=b.amount, units=b.units, status=b.status, due_date=b.due_date) for b in bills],
        total_billed=round(sum(b.amount for b in bills), 2),
    )


@strawberry.type
class Query:
    @strawberry.field
    def me(self, info: strawberry.Info) -> UserType:
        user = _require_user(info)
        return UserType(id=user.id, name=user.name, email=user.email, role=user.role, flat_id=user.flat_id)

    @strawberry.field
    def properties(self, info: strawberry.Info, month: int, year: int) -> list[PropertyType]:
        user = _require_user(info)
        session = _session(info)
        query = select(Flat).order_by(Flat.block, Flat.flat_no)
        if user.role != "admin":
            query = query.where(Flat.id == user.flat_id)
        flats = session.scalars(query).all()
        result = []
        for flat in flats:
            score = monthly_score(session, flat.id, month, year)
            result.append(PropertyType(
                id=flat.id, flat_no=flat.flat_no, block=flat.block, type=flat.type,
                area_sqft=flat.area_sqft, resident_count=len(flat.users),
                score=int(score["total"]), badge=str(score["badge"]),
            ))
        return result

    @strawberry.field
    def tenants(self, info: strawberry.Info) -> list[TenantType]:
        user = _require_user(info)
        session = _session(info)
        query = select(User).where(User.role == "resident").order_by(User.name)
        if user.role != "admin":
            query = query.where(User.id == user.id)
        residents = session.scalars(query).all()
        return [TenantType(
            id=resident.id, name=resident.name, email=resident.email, role=resident.role,
            flat_no=resident.flat.flat_no if resident.flat else None,
        ) for resident in residents]

    @strawberry.field
    def finance_bills(self, info: strawberry.Info, month: int, year: int) -> list[FinanceBillType]:
        user = _require_user(info)
        session = _session(info)
        query = select(Bill).where(Bill.month == month, Bill.year == year).order_by(Bill.due_date, Bill.flat_id)
        if user.role != "admin":
            query = query.where(Bill.flat_id == user.flat_id)
        bills = session.scalars(query).all()
        return [FinanceBillType(
            id=bill.id, flat_no=bill.flat.flat_no, category=bill.category,
            amount=bill.amount, status=bill.status, due_date=bill.due_date,
        ) for bill in bills]

    @strawberry.field
    def maintenance_requests(self, info: strawberry.Info) -> list[MaintenanceType]:
        user = _require_user(info)
        session = _session(info)
        query = select(MaintenanceRequest).order_by(MaintenanceRequest.created_on.desc(), MaintenanceRequest.id.desc())
        if user.role != "admin":
            query = query.where(MaintenanceRequest.flat_id == user.flat_id)
        requests = session.scalars(query).all()
        return [MaintenanceType(
            id=request.id, flat_id=request.flat_id,
            flat_no=session.get(Flat, request.flat_id).flat_no,
            title=request.title, category=request.category, description=request.description,
            status=request.status, created_on=request.created_on,
        ) for request in requests]

    @strawberry.field
    def flat_report(self, info: strawberry.Info, flat_id: int, month: int, year: int) -> FlatReport | None:
        user = _require_user(info)
        session = _session(info)
        if user.role != "admin" and user.flat_id != flat_id:
            raise ValueError("Residents can only view their own flat report.")
        flat = session.get(Flat, flat_id)
        return _report(session, flat, month, year) if flat else None

    @strawberry.field
    def society_report(self, info: strawberry.Info, month: int, year: int) -> SocietyReport:
        _require_admin(info)
        session = _session(info)
        flats = session.scalars(select(Flat).order_by(Flat.flat_no)).all()
        reports = [_report(session, flat, month, year) for flat in flats]
        amounts = session.execute(
            select(Bill.status, func.sum(Bill.amount))
            .where(Bill.month == month, Bill.year == year)
            .group_by(Bill.status)
        ).all()
        by_status = {status: float(total or 0) for status, total in amounts}
        total = round(sum(by_status.values()), 2)
        doom_count = sum(report.score < 50 for report in reports)
        return SocietyReport(
            month=month, year=year,
            average_score=society_average([report.score for report in reports]),
            flat_count=len(flats), total_billed=total,
            collected=round(by_status.get("paid", 0.0), 2),
            pending=round(by_status.get("pending", 0.0), 2),
            doom_zone_count=doom_count,
        )

    @strawberry.field
    def leaderboard(self, info: strawberry.Info, month: int, year: int) -> list[FlatSummary]:
        _require_user(info)
        session = _session(info)
        flats = session.scalars(select(Flat)).all()
        rows = []
        for flat in flats:
            result = monthly_score(session, flat.id, month, year)
            rows.append(FlatSummary(flat_id=flat.id, flat_no=flat.flat_no, score=int(result["total"]), badge=str(result["badge"])))
        rows.sort(key=lambda row: (-row.score, row.flat_no))
        return rows

    @strawberry.field
    def usage_trend(self, info: strawberry.Info, flat_id: int, category: str, months: int = 6) -> list[UsagePoint]:
        user = _require_user(info)
        if user.role != "admin" and user.flat_id != flat_id:
            raise ValueError("Residents can only view their own flat usage.")
        if category not in {"electricity", "water"}:
            raise ValueError("Usage trends are available for electricity and water.")
        if not 1 <= months <= 24:
            raise ValueError("months must be between 1 and 24")
        session = _session(info)
        bills = session.scalars(
            select(Bill).where(Bill.flat_id == flat_id, Bill.category == category, Bill.units.is_not(None))
        ).all()
        bills.sort(key=lambda bill: (bill.year, bill.month))
        return [UsagePoint(month=bill.month, year=bill.year, units=float(bill.units or 0)) for bill in bills[-months:]]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def login(self, info: strawberry.Info, email: str, password: str) -> LoginResult:
        user = authenticate_user(_session(info), email, password)
        if user is None:
            return LoginResult(success=False, message="Email or password is incorrect.")
        return LoginResult(
            success=True,
            message="Login successful.",
            access_token=create_access_token(user.id),
            user=UserType(id=user.id, name=user.name, email=user.email, role=user.role, flat_id=user.flat_id),
        )

    @strawberry.mutation
    def create_maintenance_request(
        self, info: strawberry.Info, title: str, category: str, description: str = "", flat_id: int | None = None,
    ) -> ActionResult:
        user = _require_user(info)
        session = _session(info)
        selected_flat_id = user.flat_id if user.role != "admin" else flat_id
        if not selected_flat_id or not session_has_flat(session, selected_flat_id):
            raise ValueError("Choose a valid home for this request.")
        if not title.strip() or len(title) > 120:
            raise ValueError("Enter a title between 1 and 120 characters.")
        if len(description) > 1000:
            raise ValueError("Description must be 1000 characters or fewer.")
        if category not in {"plumbing", "electrical", "elevator", "cleaning", "security", "other"}:
            raise ValueError("Choose a valid maintenance category.")
        session.add(MaintenanceRequest(
            flat_id=selected_flat_id, title=title.strip(), category=category,
            description=description.strip(), status="open",
        ))
        session.commit()
        return ActionResult(success=True, message="Maintenance request submitted.", count=1)

    @strawberry.mutation
    def update_maintenance_status(self, info: strawberry.Info, request_id: int, status: str) -> ActionResult:
        _require_admin(info)
        if status not in {"open", "in_progress", "resolved"}:
            raise ValueError("Choose a valid request status.")
        session = _session(info)
        request = session.get(MaintenanceRequest, request_id)
        if request is None:
            raise ValueError("Maintenance request was not found.")
        request.status = status
        session.commit()
        return ActionResult(success=True, message="Maintenance request updated.", count=1)

    @strawberry.mutation
    def generate_bills(self, info: strawberry.Info, month: int, year: int) -> ActionResult:
        _require_admin(info)
        if not 1 <= month <= 12:
            raise ValueError("month must be between 1 and 12")
        session = _session(info)
        existing = session.scalar(select(func.count(Bill.id)).where(Bill.month == month, Bill.year == year)) or 0
        if existing:
            raise ValueError("Bills already exist for this month. Choose another month or delete existing bills.")
        flats = session.scalars(select(Flat)).all()
        due_date = bill_due_date(year, month)
        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])
        created = 0
        for flat in flats:
            readings = session.scalars(select(MeterReading).where(MeterReading.flat_id == flat.id, MeterReading.month == month, MeterReading.year == year)).all()
            units = {reading.category: reading.units for reading in readings}
            visits = session.scalar(select(func.count(GymLog.id)).where(GymLog.flat_id == flat.id, GymLog.date >= start, GymLog.date <= end)) or 0
            charges = calculate_monthly_charges(
                units_electricity=units.get("electricity", 0),
                units_water=units.get("water", 0),
                area_sqft=flat.area_sqft,
                gym_visits=visits,
            )
            for category, amount in charges.items():
                if category == "total":
                    continue
                session.add(Bill(flat_id=flat.id, month=month, year=year, category=category, amount=amount, units=units.get(category), status="pending", due_date=due_date))
                created += 1
        session.commit()
        return ActionResult(success=True, message=f"Bills generated for {date(year, month, 1):%B %Y}", count=created)

    @strawberry.mutation
    def add_points(self, info: strawberry.Info, flat_id: int, category: str, points: int, note: str = "", month: int | None = None, year: int | None = None) -> ActionResult:
        _require_admin(info)
        if category not in CATEGORY_MAXIMUMS:
            raise ValueError("category must be cleanliness, discipline, or events")
        today = date.today()
        month, year = month or today.month, year or today.year
        if not 1 <= month <= 12 or not session_has_flat(_session(info), flat_id):
            raise ValueError("Choose a valid month and flat.")
        session = _session(info)
        session.add(PointEntry(flat_id=flat_id, category=category, points=points, note=note, month=month, year=year))
        session.commit()
        return ActionResult(success=True, message="Points saved.", count=1)

    @strawberry.mutation
    def add_meter_reading(self, info: strawberry.Info, flat_id: int, month: int, year: int, category: str, units: float) -> ActionResult:
        _require_admin(info)
        if category not in {"electricity", "water"}:
            raise ValueError("category must be electricity or water")
        if units < 0 or not 1 <= month <= 12:
            raise ValueError("Enter non-negative units and a valid month.")
        session = _session(info)
        if not session_has_flat(session, flat_id):
            raise ValueError("Flat was not found.")
        reading = session.scalar(select(MeterReading).where(MeterReading.flat_id == flat_id, MeterReading.month == month, MeterReading.year == year, MeterReading.category == category))
        if reading:
            reading.units = units
        else:
            session.add(MeterReading(flat_id=flat_id, month=month, year=year, category=category, units=units))
        session.commit()
        return ActionResult(success=True, message="Meter reading saved.", count=1)

    @strawberry.mutation
    def log_gym(self, info: strawberry.Info, flat_id: int, visit_date: date, minutes: int) -> ActionResult:
        _require_admin(info)
        if minutes <= 0:
            raise ValueError("Minutes must be greater than zero.")
        session = _session(info)
        if not session_has_flat(session, flat_id):
            raise ValueError("Flat was not found.")
        session.add(GymLog(flat_id=flat_id, date=visit_date, minutes=minutes))
        session.commit()
        return ActionResult(success=True, message="Gym log saved.", count=1)

    @strawberry.mutation
    def mark_bill_paid(self, info: strawberry.Info, bill_id: int) -> ActionResult:
        user = _require_user(info)
        session = _session(info)
        bill = session.get(Bill, bill_id)
        if not bill:
            raise ValueError("Bill was not found.")
        if user.role != "admin" and user.flat_id != bill.flat_id:
            raise ValueError("Residents can only update their own flat's bills.")
        bill.status = "paid"
        session.commit()
        return ActionResult(success=True, message="Bill marked as paid.", count=1)


def session_has_flat(session: Session, flat_id: int) -> bool:
    return session.get(Flat, flat_id) is not None


schema = strawberry.Schema(query=Query, mutation=Mutation)
