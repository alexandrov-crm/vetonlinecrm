from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_session
from app.models.doctor import Doctor
from app.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def get_current_doctor(request: Request, session: AsyncSession = Depends(get_session)) -> Doctor:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Не авторизован")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Токен истёк")

    doctor_id = payload.get("doctor_id")
    result = await session.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()

    if not doctor or not doctor.is_active:
        raise HTTPException(status_code=401, detail="Врач не найден")

    return doctor


async def get_current_admin(doctor: Doctor = Depends(get_current_doctor)) -> Doctor:
    if not doctor.is_admin:
        raise HTTPException(status_code=403, detail="Только для администратора")
    return doctor


# === /api/auth/me — ЭТОГО НЕ ХВАТАЛО ===
@router.get("/me")
async def get_me(doctor: Doctor = Depends(get_current_doctor)):
    return {
        "id": doctor.id,
        "username": doctor.username,
        "full_name": doctor.full_name,
        "email": doctor.email,
        "specialization": doctor.specialization or "",
        "phone": doctor.phone or "",
        "is_admin": doctor.is_admin,
        "is_active": doctor.is_active
    }


@router.post("/login")
async def login(request: Request, session: AsyncSession = Depends(get_session)):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    result = await session.execute(select(Doctor).where(Doctor.username == username))
    doctor = result.scalar_one_or_none()

    if not doctor or not verify_password(password, doctor.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    if not doctor.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт деактивирован")

    token = create_access_token({"doctor_id": doctor.id, "is_admin": doctor.is_admin})
    response = Response()
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=86400)
    response.headers["location"] = "/dashboard"
    response.status_code = 303
    return response


@router.post("/logout")
async def logout():
    response = Response()
    response.delete_cookie("access_token")
    response.headers["location"] = "/login"
    response.status_code = 303
    return response


# === ADMIN: Создание врача ===
@router.post("/doctors/create")
async def create_doctor(
    request: Request,
    session: AsyncSession = Depends(get_session),
    admin: Doctor = Depends(get_current_admin)
):
    form = await request.form()
    username = form.get("username", "").strip()
    password = form.get("password", "").strip()
    full_name = form.get("full_name", "").strip()
    email = form.get("email", "").strip()
    specialization = form.get("specialization", "").strip()
    phone = form.get("phone", "").strip()

    if not username or not password or not full_name or not email:
        raise HTTPException(status_code=400, detail="Заполните все обязательные поля")

    existing = await session.execute(select(Doctor).where(
        (Doctor.username == username) | (Doctor.email == email)
    ))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким логином или email уже существует")

    doctor = Doctor(
        username=username,
        hashed_password=hash_password(password),
        full_name=full_name,
        email=email,
        specialization=specialization,
        phone=phone,
        is_active=True,
        is_admin=False
    )
    session.add(doctor)
    await session.flush()

    response = Response()
    response.headers["location"] = "/admin/doctors"
    response.status_code = 303
    return response


# === ADMIN: Список врачей ===
@router.get("/doctors/list")
async def list_doctors(
    session: AsyncSession = Depends(get_session),
    admin: Doctor = Depends(get_current_admin)
):
    result = await session.execute(select(Doctor).where(Doctor.is_admin == False))
    doctors = result.scalars().all()
    return [
        {
            "id": d.id,
            "username": d.username,
            "full_name": d.full_name,
            "email": d.email,
            "specialization": d.specialization,
            "phone": d.phone,
            "is_active": d.is_active
        }
        for d in doctors
    ]


# === ADMIN: Деактивировать/активировать врача ===
@router.post("/doctors/{doctor_id}/toggle")
async def toggle_doctor(
    doctor_id: int,
    session: AsyncSession = Depends(get_session),
    admin: Doctor = Depends(get_current_admin)
):
    result = await session.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Врач не найден")

    doctor.is_active = not doctor.is_active
    await session.flush()
    return {"status": "ok", "is_active": doctor.is_active}
