from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from app.database import get_session
from app.models.doctor import Doctor
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.calendar import CalendarSlot
from app.models.settings import DoctorSettings
from app.routers.auth import get_current_doctor

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("")
async def get_calendar(
    date: str = None,
    week: str = None,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    """Получить слоты календаря на день или неделю"""

    # Получаем настройки врача
    settings_result = await session.execute(
        select(DoctorSettings).where(DoctorSettings.doctor_id == doctor.id)
    )
    doc_settings = settings_result.scalar_one_or_none()
    work_start = doc_settings.work_start_hour if doc_settings else 9
    work_end = doc_settings.work_end_hour if doc_settings else 21

    if week:
        try:
            start_date = datetime.strptime(week, "%Y-%m-%d")
        except ValueError:
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date -= timedelta(days=start_date.weekday())

        end_date = start_date + timedelta(days=7)
    elif date:
        try:
            start_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    else:
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date -= timedelta(days=start_date.weekday())
        end_date = start_date + timedelta(days=7)

    result = await session.execute(
        select(CalendarSlot).where(
            CalendarSlot.doctor_id == doctor.id,
            CalendarSlot.date >= start_date,
            CalendarSlot.date < end_date
        ).options(
            selectinload(CalendarSlot.pet).selectinload(Pet.owner)
        ).order_by(CalendarSlot.date, CalendarSlot.hour)
    )
    slots = result.scalars().all()

    return {
        "work_start": work_start,
        "work_end": work_end,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "slots": [{
            "id": s.id,
            "date": s.date.strftime("%Y-%m-%d"),
            "hour": s.hour,
            "status": s.status,
            "notes": s.notes,
            "pet": {
                "id": s.pet.id,
                "name": s.pet.name,
                "species": s.pet.species,
                "owner_name": s.pet.owner.full_name,
                "owner_phone": s.pet.owner.phone
            } if s.pet else None
        } for s in slots]
    }


@router.post("")
async def create_slot(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    """Записать пациента в слот"""
    data = await request.json()

    date_str = data.get("date")
    hour = data.get("hour")

    if not date_str or hour is None:
        raise HTTPException(status_code=400, detail="Дата и час обязательны")

    try:
        slot_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты")

    # Проверяем нет ли уже слота
    existing = await session.execute(
        select(CalendarSlot).where(
            CalendarSlot.doctor_id == doctor.id,
            CalendarSlot.date == slot_date,
            CalendarSlot.hour == hour
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Этот слот уже занят")

    pet_id = data.get("pet_id")
    if pet_id:
        pet_result = await session.execute(
            select(Pet).join(Owner).where(
                Pet.id == pet_id,
                Owner.doctor_id == doctor.id
            )
        )
        if not pet_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Питомец не найден")

    slot = CalendarSlot(
        doctor_id=doctor.id,
        pet_id=pet_id,
        date=slot_date,
        hour=hour,
        status="booked" if pet_id else "free",
        notes=data.get("notes", "")
    )
    session.add(slot)
    await session.flush()

    return {
        "message": "Запись создана",
        "slot": {"id": slot.id, "date": date_str, "hour": hour, "status": slot.status}
    }


@router.put("/{slot_id}")
async def update_slot(
    slot_id: int,
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(CalendarSlot).where(
            CalendarSlot.id == slot_id,
            CalendarSlot.doctor_id == doctor.id
        )
    )
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Слот не найден")

    data = await request.json()

    if "pet_id" in data:
        slot.pet_id = data["pet_id"]
        slot.status = "booked" if data["pet_id"] else "free"
    if "status" in data:
        slot.status = data["status"]
    if "notes" in data:
        slot.notes = data["notes"]

    return {"message": "Запись обновлена"}


@router.delete("/{slot_id}")
async def delete_slot(
    slot_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(CalendarSlot).where(
            CalendarSlot.id == slot_id,
            CalendarSlot.doctor_id == doctor.id
        )
    )
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Слот не найден")

    await session.delete(slot)
    return {"message": "Запись удалена"}
