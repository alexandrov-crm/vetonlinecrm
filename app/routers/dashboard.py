from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.database import get_session
from app.models.doctor import Doctor
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.visit import Visit
from app.models.calendar import CalendarSlot
from app.models.reminder import Reminder
from app.models.intake import Intake
from app.models.questionnaire import Questionnaire
from app.routers.auth import get_current_doctor

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start.replace(hour=23, minute=59, second=59)
    week_start = today_start - timedelta(days=today_start.weekday())
    week_end = week_start + timedelta(days=7)

    # Общая статистика
    owners_count = await session.execute(
        select(func.count(Owner.id)).where(Owner.doctor_id == doctor.id)
    )
    pets_count = await session.execute(
        select(func.count(Pet.id)).join(Owner).where(Owner.doctor_id == doctor.id)
    )
    visits_count = await session.execute(
        select(func.count(Visit.id)).where(Visit.doctor_id == doctor.id)
    )

    # Приёмы сегодня
    today_visits = await session.execute(
        select(func.count(CalendarSlot.id)).where(
            CalendarSlot.doctor_id == doctor.id,
            CalendarSlot.date >= today_start,
            CalendarSlot.date <= today_end,
            CalendarSlot.status == "booked"
        )
    )

    # Ближайшие приёмы
    upcoming_result = await session.execute(
        select(CalendarSlot).where(
            CalendarSlot.doctor_id == doctor.id,
            CalendarSlot.date >= today_start,
            CalendarSlot.date <= today_start + timedelta(days=2),
            CalendarSlot.status == "booked",
            CalendarSlot.pet_id != None
        ).order_by(CalendarSlot.date, CalendarSlot.hour).limit(5)
    )
    upcoming_slots = upcoming_result.scalars().all()

    upcoming = []
    for slot in upcoming_slots:
        if slot.pet_id:
            pet_result = await session.execute(
                select(Pet).where(Pet.id == slot.pet_id)
            )
            pet = pet_result.scalar_one_or_none()
            if pet:
                owner_result = await session.execute(
                    select(Owner).where(Owner.id == pet.owner_id)
                )
                owner = owner_result.scalar_one_or_none()
                upcoming.append({
                    "slot_id": slot.id,
                    "date": slot.date.strftime("%Y-%m-%d"),
                    "hour": slot.hour,
                    "pet_name": pet.name,
                    "pet_species": pet.species,
                    "owner_name": owner.full_name if owner else "",
                    "owner_phone": owner.phone if owner else ""
                })

    # Напоминания на сегодня
    reminders_result = await session.execute(
        select(Reminder).where(
            Reminder.doctor_id == doctor.id,
            Reminder.remind_date >= today_start,
            Reminder.remind_date <= today_end,
            Reminder.is_done == False
        ).order_by(Reminder.remind_date.asc())
    )
    reminders = reminders_result.scalars().all()

    # Новые анкеты
    new_intakes = await session.execute(
        select(func.count(Intake.id)).join(Questionnaire).where(
            Questionnaire.doctor_id == doctor.id,
            Intake.status == "new"
        )
    )

    # Визиты за неделю
    week_visits = await session.execute(
        select(func.count(Visit.id)).where(
            Visit.doctor_id == doctor.id,
            Visit.created_at >= week_start,
            Visit.created_at <= week_end
        )
    )

    return {
        "stats": {
            "total_owners": owners_count.scalar() or 0,
            "total_pets": pets_count.scalar() or 0,
            "total_visits": visits_count.scalar() or 0,
            "today_visits": today_visits.scalar() or 0,
            "week_visits": week_visits.scalar() or 0,
            "new_intakes": new_intakes.scalar() or 0
        },
        "upcoming": upcoming,
        "reminders": [{
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "remind_date": r.remind_date.isoformat() if r.remind_date else None,
            "reminder_type": r.reminder_type
        } for r in reminders],
        "doctor": {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "is_admin": doctor.is_admin
        }
    }
