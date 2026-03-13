from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_session
from app.models.doctor import Doctor
from app.routers.auth import get_current_doctor
from app.services.auth_service import hash_password

router = APIRouter(prefix="/api/doctors", tags=["doctors"])


@router.get("")
async def get_doctors(
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    """Список врачей (только для админа)"""
    if not doctor.is_admin:
        raise HTTPException(status_code=403, detail="Только для админа")

    result = await session.execute(select(Doctor).order_by(Doctor.created_at.desc()))
    doctors = result.scalars().all()

    return [{
        "id": d.id,
        "email": d.email,
        "username": d.username,
        "full_name": d.full_name,
        "phone": d.phone,
        "specialization": d.specialization,
        "is_active": d.is_active,
        "is_admin": d.is_admin,
        "created_at": d.created_at.isoformat() if d.created_at else None
    } for d in doctors]


@router.post("")
async def create_doctor(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    """Создать нового врача (только админ)"""
    if not doctor.is_admin:
        raise HTTPException(status_code=403, detail="Только для админа")

    data = await request.json()

    email = data.get("email", "").strip().lower()
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()

    if not all([email, username, password, full_name]):
        raise HTTPException(status_code=400, detail="Заполните все обязательные поля")

    result = await session.execute(select(Doctor).where(
        (Doctor.email == email) | (Doctor.username == username)
    ))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email или логин уже заняты")

    from app.models.settings import DoctorSettings

    new_doctor = Doctor(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        full_name=full_name,
        phone=data.get("phone", ""),
        specialization=data.get("specialization", ""),
        is_admin=False,
        is_active=True
    )
    session.add(new_doctor)
    await session.flush()

    settings = DoctorSettings(
        doctor_id=new_doctor.id,
        work_start_hour=9,
        work_end_hour=21,
        slot_duration=60,
        theme="light"
    )
    session.add(settings)

    return {
        "message": "Врач создан",
        "doctor": {
            "id": new_doctor.id,
            "full_name": new_doctor.full_name,
            "email": new_doctor.email,
            "username": new_doctor.username
        }
    }


@router.put("/{doctor_id}")
async def update_doctor(
    doctor_id: int,
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    """Обновить врача"""
    if not doctor.is_admin and doctor.id != doctor_id:
        raise HTTPException(status_code=403, detail="Нет доступа")

    result = await session.execute(select(Doctor).where(Doctor.id == doctor_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Врач не найден")

    data = await request.json()

    if data.get("full_name"):
        target.full_name = data["full_name"]
    if data.get("phone") is not None:
        target.phone = data["phone"]
    if data.get("specialization") is not None:
        target.specialization = data["specialization"]
    if data.get("email"):
        target.email = data["email"].strip().lower()
    if data.get("password"):
        target.hashed_password = hash_password(data["password"])
    if doctor.is_admin and "is_active" in data:
        target.is_active = data["is_active"]

    return {"message": "Данные обновлены"}


@router.delete("/{doctor_id}")
async def delete_doctor(
    doctor_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    """Удалить врача (только админ)"""
    if not doctor.is_admin:
        raise HTTPException(status_code=403, detail="Только для админа")

    if doctor.id == doctor_id:
        raise HTTPException(status_code=400, detail="Нельзя удалить себя")

    result = await session.execute(select(Doctor).where(Doctor.id == doctor_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Врач не найден")

    await session.delete(target)
    return {"message": "Врач удалён"}
