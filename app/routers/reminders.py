from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_session
from app.models.doctor import Doctor
from app.models.reminder import Reminder
from app.routers.auth import get_current_doctor

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("")
async def get_reminders(
    date: str = None,
    is_done: bool = None,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    query = select(Reminder).where(Reminder.doctor_id == doctor.id)

    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
            next_date = target_date.replace(hour=23, minute=59, second=59)
            query = query.where(
                Reminder.remind_date >= target_date,
                Reminder.remind_date <= next_date
            )
        except ValueError:
            pass

    if is_done is not None:
        query = query.where(Reminder.is_done == is_done)

    query = query.order_by(Reminder.remind_date.asc())
    result = await session.execute(query)
    reminders = result.scalars().all()

    return [{
        "id": r.id,
        "title": r.title,
        "description": r.description,
        "remind_date": r.remind_date.isoformat() if r.remind_date else None,
        "is_done": r.is_done,
        "reminder_type": r.reminder_type,
        "pet_id": r.pet_id,
        "created_at": r.created_at.isoformat() if r.created_at else None
    } for r in reminders]


@router.get("/today")
async def get_today_reminders(
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start.replace(hour=23, minute=59, second=59)

    result = await session.execute(
        select(Reminder).where(
            Reminder.doctor_id == doctor.id,
            Reminder.remind_date >= today_start,
            Reminder.remind_date <= today_end,
            Reminder.is_done == False
        ).order_by(Reminder.remind_date.asc())
    )
    reminders = result.scalars().all()

    return [{
        "id": r.id,
        "title": r.title,
        "description": r.description,
        "remind_date": r.remind_date.isoformat() if r.remind_date else None,
        "reminder_type": r.reminder_type,
        "pet_id": r.pet_id
    } for r in reminders]


@router.post("")
async def create_reminder(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    data = await request.json()

    title = data.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Заголовок обязателен")

    remind_date = None
    if data.get("remind_date"):
        try:
            remind_date = datetime.fromisoformat(data["remind_date"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат даты")
    else:
        raise HTTPException(status_code=400, detail="Дата напоминания обязательна")

    reminder = Reminder(
        doctor_id=doctor.id,
        pet_id=data.get("pet_id"),
        title=title,
        description=data.get("description", ""),
        remind_date=remind_date,
        reminder_type=data.get("reminder_type", "custom")
    )
    session.add(reminder)
    await session.flush()

    return {
        "message": "Напоминание создано",
        "reminder": {"id": reminder.id, "title": reminder.title}
    }


@router.put("/{reminder_id}")
async def update_reminder(
    reminder_id: int,
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.doctor_id == doctor.id
        )
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Напоминание не найдено")

    data = await request.json()

    if data.get("title"):
        reminder.title = data["title"]
    if "description" in data:
        reminder.description = data["description"]
    if data.get("remind_date"):
        try:
            reminder.remind_date = datetime.fromisoformat(data["remind_date"])
        except ValueError:
            pass
    if "is_done" in data:
        reminder.is_done = data["is_done"]
    if "reminder_type" in data:
        reminder.reminder_type = data["reminder_type"]

    return {"message": "Напоминание обновлено"}


@router.put("/{reminder_id}/done")
async def mark_done(
    reminder_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.doctor_id == doctor.id
        )
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Напоминание не найдено")

    reminder.is_done = True
    return {"message": "Отмечено как выполнено"}


@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.doctor_id == doctor.id
        )
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Напоминание не найдено")

    await session.delete(reminder)
    return {"message": "Напоминание удалено"}
