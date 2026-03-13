from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_session
from app.models.doctor import Doctor
from app.models.settings import DoctorSettings
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


@router.post("/register")
async def register(request: Request, session: AsyncSession = Depends(get_session)):
    data = await request.json()

    email = data.get("email", "").strip().lower()
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()

    if not all([email, username, password, full_name]):
        raise HTTPException(status_code=400, detail="Заполните все поля")

    # Проверка уникальности
    result = await session.execute(select(Doctor).where(
        (Doctor.email == email) | (Doctor.username == username)
    ))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email или логин уже заняты")

    # Первый врач — админ
    result = await session.execute(select(Doctor))
    is_first = result.first() is None

    doctor = Doctor(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        full_name=full_name,
        phone=data.get("phone", ""),
        specialization=data.get("specialization", ""),
        is_admin=is_first,
        is_active=True
    )
    session.add(doctor)
    await session.flush()

    # Создаём настройки по умолчанию
    doctor_settings = DoctorSettings(
        doctor_id=doctor.id,
        work_start_hour=9,
        work_end_hour=21,
        slot_duration=60,
        theme="light"
    )
    session.add(doctor_settings)

    token = create_access_token({"doctor_id": doctor.id})

    response = Response()
    response.status_code = 200
    response.headers["content-type"] = "application/json"
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )
    import json
    response.body = json.dumps({
        "message": "Регистрация успешна",
        "doctor": {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "email": doctor.email,
            "is_admin": doctor.is_admin
        }
    }).encode()

    return response


@router.post("/login")
async def login(request: Request, session: AsyncSession = Depends(get_session)):
    data = await request.json()

    username = data.get("username", "").strip().lower()
    password = data.get("password", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Введите логин и пароль")

    result = await session.execute(select(Doctor).where(
        (Doctor.username == username) | (Doctor.email == username)
    ))
    doctor = result.scalar_one_or_none()

    if not doctor or not verify_password(password, doctor.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    if not doctor.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт деактивирован")

    token = create_access_token({"doctor_id": doctor.id})

    response = Response()
    response.status_code = 200
    response.headers["content-type"] = "application/json"
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )
    import json
    response.body = json.dumps({
        "message": "Вход выполнен",
        "doctor": {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "email": doctor.email,
            "is_admin": doctor.is_admin
        }
    }).encode()

    return response


@router.post("/logout")
async def logout():
    response = Response()
    response.status_code = 200
    response.headers["content-type"] = "application/json"
    response.delete_cookie("access_token")
    import json
    response.body = json.dumps({"message": "Выход выполнен"}).encode()
    return response


@router.get("/me")
async def get_me(doctor: Doctor = Depends(get_current_doctor)):
    return {
        "id": doctor.id,
        "email": doctor.email,
        "username": doctor.username,
        "full_name": doctor.full_name,
        "phone": doctor.phone,
        "specialization": doctor.specialization,
        "is_admin": doctor.is_admin
    }
